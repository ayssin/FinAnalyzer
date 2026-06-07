"""
Модуль загрузки данных для российских акций
Использует MOEX API для цены + yfinance для мультипликаторов
"""

import requests
import yfinance as yf
from typing import Dict, List


class RussiaStockFetcher:
    """Работа с российскими акциями через MOEX API + yfinance"""
    
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss"
    
    def get_current_price_moex(self, ticker: str) -> float:
        """Получает цену через MOEX API (надёжно)"""
        ticker_clean = ticker.replace('.ME', '').upper()
        url = f"{self.base_url}/engines/stock/markets/shares/boards/tqbr/securities/{ticker_clean}.json"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'securities' in data and 'data' in data['securities']:
                for row in data['securities']['data']:
                    if len(row) > 3:
                        try:
                            price = float(row[3])
                            if price > 0:
                                return price
                        except:
                            pass
            return 0.0
        except Exception as e:
            print(f"Ошибка получения цены: {e}")
            return 0.0
    
    def get_ratios_from_yfinance(self, ticker: str) -> Dict:
        """Получает мультипликаторы через yfinance с суффиксом .ME"""
        ticker_with_me = ticker.replace('.ME', '').upper() + '.ME'
        
        try:
            stock = yf.Ticker(ticker_with_me)
            info = stock.info
            
            return {
                'p_e': info.get('trailingPE'),
                'p_b': info.get('priceToBook'),
                'roe': info.get('returnOnEquity'),
                'eps': info.get('trailingEps'),
                'dividend_yield': info.get('dividendYield'),
                'market_cap': info.get('marketCap'),
            }
        except Exception as e:
            print(f"Ошибка получения мультипликаторов через yfinance: {e}")
            return {}
    
    def get_security_info(self, ticker: str) -> Dict:
        """Получает информацию о компании через MOEX"""
        ticker_clean = ticker.replace('.ME', '').upper()
        url = f"{self.base_url}/engines/stock/markets/shares/boards/tqbr/securities/{ticker_clean}.json"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            info = {
                'ticker': ticker_clean,
                'name': ticker_clean,
                'shortname': ticker_clean,
                'currency': 'RUB',
            }
            
            if 'securities' in data and 'data' in data['securities']:
                for row in data['securities']['data']:
                    if len(row) > 2:
                        info['shortname'] = row[2] if len(row) > 2 else ticker_clean
                        info['name'] = row[9] if len(row) > 9 else info['shortname']
                        break
            
            return info
        except Exception as e:
            return {'ticker': ticker_clean, 'name': ticker_clean, 'shortname': ticker_clean, 'currency': 'RUB'}
    
    def get_historical_prices(self, ticker: str, days: int = 180) -> List:
        """Получает исторические цены через MOEX API"""
        ticker_clean = ticker.replace('.ME', '').upper()
        url = f"{self.base_url}/history/engines/stock/markets/shares/boards/tqbr/securities/{ticker_clean}.json"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'history' in data and 'data' in data['history']:
                prices = []
                for row in data['history']['data'][:days]:
                    if len(row) > 3:
                        try:
                            date = row[0]
                            price = float(row[3])
                            prices.append((date, price))
                        except:
                            pass
                return prices
            return []
        except Exception as e:
            print(f"Ошибка получения истории цен: {e}")
            return []
    
    def get_competitors(self, ticker: str) -> List:
        """Возвращает список конкурентов для сравнения"""
        competitors_map = {
            'SBER': ['VTBR', 'TCSG'],
            'GAZP': ['LKOH', 'ROSN'],
            'LKOH': ['GAZP', 'ROSN'],
            'ROSN': ['GAZP', 'LKOH'],
            'YNDX': ['OZON'],
            'MGNT': ['X5'],
            'GMKN': ['CHMF', 'NLMK'],
            'TATN': ['LKOH', 'ROSN'],
            'NVTK': ['GAZP', 'LKOH'],
        }
        return competitors_map.get(ticker.replace('.ME', '').upper(), [])
    
    def get_competitors_data(self, ticker: str) -> List:
        """Получает данные по конкурентам"""
        competitors = self.get_competitors(ticker)
        competitors_data = []
        
        for comp in competitors:
            comp_clean = comp.replace('.ME', '').upper()
            info = self.get_security_info(comp_clean)
            ratios = self.get_ratios_from_yfinance(comp_clean)
            price = self.get_current_price_moex(comp_clean)
            
            competitors_data.append({
                'ticker': comp_clean,
                'name': info.get('shortname', comp_clean),
                'price': price,
                'p_e': ratios.get('p_e'),
                'p_b': ratios.get('p_b'),
                'roe': ratios.get('roe') * 100 if ratios.get('roe') else None,
            })
        
        return competitors_data
    
    def get_all_data(self, ticker: str) -> Dict:
        """Получает все данные для российского тикера"""
        ticker_clean = ticker.replace('.ME', '').upper()
        
        print(f"Загрузка данных для {ticker_clean}...")
        
        price = self.get_current_price_moex(ticker_clean)
        print(f"  Цена: {price} RUB")
        
        info = self.get_security_info(ticker_clean)
        ratios = self.get_ratios_from_yfinance(ticker_clean)
        competitors = self.get_competitors_data(ticker_clean)
        
        if ratios.get('p_e'):
            print(f"  P/E: {ratios['p_e']:.2f}")
        if ratios.get('p_b'):
            print(f"  P/B: {ratios['p_b']:.2f}")
        if ratios.get('roe'):
            print(f"  ROE: {ratios['roe']*100:.2f}%")
        
        return {
            'ticker': ticker,
            'price': price,
            'market_cap': ratios.get('market_cap', 0),
            'sector': 'Российский рынок',
            'industry': info.get('name', ticker_clean),
            'shortname': info.get('shortname', ticker_clean),
            'currency': 'RUB',
            'exchange': 'MOEX',
            'company_name': info.get('name', ticker_clean),
            'p_e': ratios.get('p_e'),
            'p_b': ratios.get('p_b'),
            'roe': ratios.get('roe') * 100 if ratios.get('roe') else None,
            'eps': ratios.get('eps'),
            'dividend_yield': ratios.get('dividend_yield'),
            'competitors': competitors,
        }


def get_russian_stock_data(ticker: str) -> Dict:
    """Получить данные по российским акциям"""
    fetcher = RussiaStockFetcher()
    return fetcher.get_all_data(ticker)


if __name__ == "__main__":
    ticker = 'SBER'
    data = get_russian_stock_data(ticker)
    
    print(f"\n{'='*50}")
    print(f"ИТОГОВЫЕ ДАННЫЕ ДЛЯ {ticker}")
    print(f"{'='*50}")
    print(f"Компания: {data.get('company_name')}")
    print(f"Цена: {data.get('price')} RUB")
    print(f"P/E: {data.get('p_e')}")
    print(f"P/B: {data.get('p_b')}")
    print(f"ROE: {data.get('roe')}%")
    print(f"Конкуренты: {len(data.get('competitors', []))}")
