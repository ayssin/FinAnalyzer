"""
Модуль загрузки финансовой отчётности
Загружает данные из yfinance, кэширует на диск
"""

import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, Tuple


def get_financials(ticker: str, use_cache: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Загружает три финансовых отчёта для тикера
    Для российских тикеров (.ME) возвращает пустые DataFrame
    """
    
    # Проверяем, российский ли тикер
    ticker_upper = ticker.upper()
    is_russian = ticker_upper.endswith('.ME') or ticker_upper in [
        'SBER', 'VTBR', 'TCSG', 'GAZP', 'LKOH', 'ROSN', 'TATN', 'NVTK',
        'YNDX', 'MGNT', 'GMKN', 'CHMF', 'NLMK', 'MAGN', 'ALRS',
        'MOEX', 'OZON', 'AFKS'
    ]
    
    if is_russian:
        print(f"🇷🇺 Российский тикер {ticker}: фундаментальные данные не доступны")
        print(f"   Доступна только цена акции")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    cache_file = f"data/{ticker}_financials.json"
    
    if use_cache and os.path.exists(cache_file):
        print(f"📦 Загружаем из кэша: {ticker}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        income = pd.DataFrame(cached.get('income', {})) if cached.get('income') else pd.DataFrame()
        balance = pd.DataFrame(cached.get('balance', {})) if cached.get('balance') else pd.DataFrame()
        cashflow = pd.DataFrame(cached.get('cashflow', {})) if cached.get('cashflow') else pd.DataFrame()
        
        for df in [income, balance, cashflow]:
            if not df.empty:
                df.index = pd.to_datetime(df.index)
        
        return income, balance, cashflow
    
    print(f"🌐 Загружаем данные для {ticker} из yfinance...")
    
    stock = yf.Ticker(ticker)
    
    try:
        income_raw = stock.financials
        balance_raw = stock.balance_sheet
        cashflow_raw = stock.cashflow
        
        if income_raw.empty or balance_raw.empty or cashflow_raw.empty:
            raise ValueError(f"Нет данных для тикера {ticker}")
        
        income = income_raw.T.copy()
        balance = balance_raw.T.copy()
        cashflow = cashflow_raw.T.copy()
        
        income_index = income.index
        balance_index = balance.index
        cashflow_index = cashflow.index
        
        income.index = income.index.strftime('%Y-%m-%d')
        balance.index = balance.index.strftime('%Y-%m-%d')
        cashflow.index = cashflow.index.strftime('%Y-%m-%d')
        
        def df_to_dict(df):
            df_clean = df.where(pd.notna(df), None)
            return df_clean.to_dict()
        
        os.makedirs("data", exist_ok=True)
        cache_data = {
            'income': df_to_dict(income),
            'balance': df_to_dict(balance),
            'cashflow': df_to_dict(cashflow),
            'date': datetime.now().isoformat()
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Данные загружены и сохранены в кэш: {cache_file}")
        
        income.index = income_index
        balance.index = balance_index
        cashflow.index = cashflow_index
        
        return income, balance, cashflow
        
    except Exception as e:
        print(f"❌ Ошибка загрузки данных для {ticker}: {e}")
        raise


def get_market_data(ticker: str) -> Dict:
    """Получает рыночные данные, поддерживая US и RU рынки (.ME)"""
    print(f"🌐 Загружаем рыночные данные для {ticker}...")
    
    ticker_upper = ticker.upper()
    is_russian = ticker_upper.endswith('.ME') or ticker_upper in [
        'SBER', 'VTBR', 'TCSG', 'GAZP', 'LKOH', 'ROSN', 'YNDX', 'MGNT'
    ]
    
    stock = yf.Ticker(ticker)
    info = stock.info
    
    market_data = {
        'ticker': ticker,
        'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
        'shares_outstanding': info.get('sharesOutstanding', 0),
        'market_cap': info.get('marketCap', 0),
        'sector': info.get('sector', 'Российский рынок' if is_russian else 'Unknown'),
        'industry': info.get('industry', 'Мосбиржа' if is_russian else 'Unknown'),
        'currency': info.get('financialCurrency', 'RUB' if is_russian else 'USD'),
        'exchange': 'MOEX' if is_russian else info.get('exchange', 'Unknown')
    }
    
    if market_data['price']:
        currency_symbol = '₽' if is_russian else '$'
        print(f"✅ Цена: {currency_symbol}{market_data['price']:.2f}")
        if market_data['market_cap'] and market_data['market_cap'] > 0:
            print(f"   Капитализация: {currency_symbol}{market_data['market_cap']/1e9:.1f} млрд")
    
    return market_data


def get_all_data(ticker: str) -> Dict:
    """Получает все данные за один раз"""
    print(f"\n{'='*50}")
    print(f"Анализ компании: {ticker.upper()}")
    print(f"{'='*50}\n")
    
    income, balance, cashflow = get_financials(ticker)
    market = get_market_data(ticker)
    
    return {
        'ticker': ticker,
        'income_stmt': income,
        'balance_sheet': balance,
        'cash_flow': cashflow,
        'market_data': market
    }
