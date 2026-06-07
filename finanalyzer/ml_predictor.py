"""
Модуль ML прогнозирования цен акций
Использует Random Forest для предсказания движения цены
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, Tuple, Optional


class MLPredictor:
    """ML модель для прогнозирования цен акций"""
    
    def __init__(self):
        self.regressor = None
        self.classifier = None
        self.last_price = 0
        self.feature_names = []
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Создаёт признаки для ML модели
        """
        data = df.copy()
        
        # Лаги цены (цена за предыдущие дни)
        data['price_lag1'] = data['Close'].shift(1)
        data['price_lag2'] = data['Close'].shift(2)
        data['price_lag3'] = data['Close'].shift(3)
        data['price_lag5'] = data['Close'].shift(5)
        
        # Скользящие средние
        data['ma_5'] = data['Close'].rolling(5).mean()
        data['ma_10'] = data['Close'].rolling(10).mean()
        data['ma_20'] = data['Close'].rolling(20).mean()
        
        # Отношение к скользящим средним
        data['price_to_ma5'] = data['Close'] / data['ma_5']
        data['price_to_ma20'] = data['Close'] / data['ma_20']
        
        # RSI (Relative Strength Index)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Волатильность (стандартное отклонение за 5 дней)
        data['volatility_5'] = data['Close'].rolling(5).std()
        data['volatility_20'] = data['Close'].rolling(20).std()
        
        # Объём торгов (относительный)
        data['volume_ma'] = data['Volume'].rolling(10).mean()
        data['volume_ratio'] = data['Volume'] / data['volume_ma']
        
        # Дневная доходность
        data['daily_return'] = data['Close'].pct_change()
        data['return_lag1'] = data['daily_return'].shift(1)
        
        # Диапазон дня
        data['high_low_ratio'] = (data['High'] - data['Low']) / data['Close']
        
        # Тренд (знак изменения)
        data['trend'] = np.sign(data['daily_return'])
        
        # Удаляем строки с NaN
        data = data.dropna()
        
        return data
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Подготавливает признаки для обучения
        """
        data = self.create_features(df)
        
        # Признаки для регрессии (прогноз цены)
        feature_cols = [col for col in data.columns if col not in ['Close', 'High', 'Low', 'Open', 'Volume', 'Adj Close']]
        
        self.feature_names = feature_cols
        X = data[feature_cols].values
        
        # Целевые переменные
        y_reg = data['Close'].values  # Регрессия: цена
        y_cls = (data['daily_return'].shift(-1) > 0).astype(int).values[:-1]  # Классификация: рост/падение
        X_cls = X[:-1]
        
        return X, y_reg, X_cls, y_cls
    
    def train(self, ticker: str, period: str = "2y") -> Dict:
        """
        Обучает модель на исторических данных
        """
        print(f"🤖 Загрузка данных для обучения модели {ticker}...")
        
        # Загружаем исторические данные
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            return {'error': f'Нет данных для {ticker}'}
        
        print(f"   Загружено {len(df)} дней данных")
        
        # Подготавливаем признаки
        X, y_reg, X_cls, y_cls = self.prepare_features(df)
        
        if len(X) < 50:
            return {'error': 'Недостаточно данных для обучения'}
        
        # Разделяем на train и test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y_reg[:split_idx], y_reg[split_idx:]
        
        # Обучаем регрессию (Random Forest)
        print("   Обучение модели регрессии...")
        self.regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.regressor.fit(X_train, y_train)
        
        # Оцениваем качество
        y_pred = self.regressor.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        score = self.regressor.score(X_test, y_test)
        
        # Обучаем классификатор (направление движения)
        if len(X_cls) > 50:
            Xc_train, Xc_test = X_cls[:split_idx], X_cls[split_idx:]
            yc_train, yc_test = y_cls[:split_idx], y_cls[split_idx:]
            
            print("   Обучение модели классификации...")
            self.classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                random_state=42,
                n_jobs=-1
            )
            self.classifier.fit(Xc_train, yc_train)
            yc_pred = self.classifier.predict(Xc_test)
            accuracy = accuracy_score(yc_test, yc_pred)
        else:
            accuracy = 0
        
        self.last_price = df['Close'].iloc[-1]
        
        return {
            'trained': True,
            'mae': round(mae, 2),
            'r2_score': round(score, 4),
            'accuracy': round(accuracy * 100, 1),
            'samples': len(X),
            'features': len(self.feature_names)
        }
    
    def predict(self, ticker: str, days: int = 5) -> Dict:
        """
        Делает прогноз на следующие дни
        """
        # Загружаем последние данные
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        if df.empty or self.regressor is None:
            return {'error': 'Модель не обучена или нет данных'}
        
        # Создаём признаки для последнего дня
        data = self.create_features(df)
        if data.empty:
            return {'error': 'Недостаточно данных для прогноза'}
        
        last_features = data.iloc[-1:][self.feature_names]
        
        # Прогноз цены
        predicted_price = self.regressor.predict(last_features)[0]
        current_price = df['Close'].iloc[-1]
        
        # Процент изменения
        change_pct = ((predicted_price - current_price) / current_price) * 100
        
        # Определяем рекомендацию
        if change_pct > 2:
            recommendation = "ПОКУПАТЬ"
            signal = "🟢"
        elif change_pct > 0:
            recommendation = "ДЕРЖАТЬ (слабый рост)"
            signal = "🟡"
        elif change_pct > -2:
            recommendation = "ДЕРЖАТЬ (слабое падение)"
            signal = "🟠"
        else:
            recommendation = "ПРОДАВАТЬ"
            signal = "🔴"
        
        # Прогноз направления (если есть классификатор)
        direction = None
        if self.classifier:
            pred_dir = self.classifier.predict(last_features)[0]
            direction = "РОСТ" if pred_dir == 1 else "ПАДЕНИЕ"
        
        return {
            'current_price': round(current_price, 2),
            'predicted_price': round(predicted_price, 2),
            'change_pct': round(change_pct, 2),
            'change_abs': round(predicted_price - current_price, 2),
            'recommendation': recommendation,
            'signal': signal,
            'direction': direction,
            'confidence_interval': {
                'lower': round(predicted_price * 0.95, 2),
                'upper': round(predicted_price * 1.05, 2)
            }
        }


def get_ml_forecast(ticker: str) -> Dict:
    """
    Упрощённая функция для получения ML прогноза
    """
    predictor = MLPredictor()
    
    # Обучаем модель
    train_result = predictor.train(ticker)
    
    if 'error' in train_result:
        return train_result
    
    # Делаем прогноз
    forecast = predictor.predict(ticker)
    forecast['model_quality'] = train_result
    
    return forecast


if __name__ == "__main__":
    # Тестирование
    ticker = "MSFT"
    print(f"🤖 ML Прогнозирование для {ticker}")
    print("="*50)
    
    result = get_ml_forecast(ticker)
    
    if 'error' in result:
        print(f"Ошибка: {result['error']}")
    else:
        print(f"\n📈 РЕЗУЛЬТАТЫ МОДЕЛИ:")
        print(f"   Качество модели (R²): {result['model_quality']['r2_score']}")
        print(f"   Средняя ошибка: ${result['model_quality']['mae']}")
        print(f"   Точность направления: {result['model_quality']['accuracy']}%")
        
        print(f"\n🎯 ПРОГНОЗ НА ЗАВТРА:")
        print(f"   Текущая цена: ${result['current_price']}")
        print(f"   Прогноз: ${result['predicted_price']}")
        print(f"   Изменение: {result['change_pct']:+}% (${result['change_abs']:+.2f})")
        print(f"   Доверительный интервал: ${result['confidence_interval']['lower']} - ${result['confidence_interval']['upper']}")
        print(f"\n   {result['signal']} РЕКОМЕНДАЦИЯ: {result['recommendation']}")
