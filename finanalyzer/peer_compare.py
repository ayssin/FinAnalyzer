"""
Модуль сравнения с отраслью
"""

import time
from typing import Dict, List
import pandas as pd

from finanalyzer.fetcher import get_all_data
from finanalyzer.ratios import calculate_ratios


PEERS_BY_SECTOR = {
    'Technology': ['AAPL', 'GOOGL', 'NVDA', 'ADBE', 'CRM', 'ORCL', 'IBM'],
    'Software - Infrastructure': ['MSFT', 'ORCL', 'IBM', 'ADBE', 'CRM'],
    'Semiconductors': ['NVDA', 'AMD', 'INTC', 'TXN', 'AVGO'],
    'Internet Content & Information': ['GOOGL', 'META', 'BIDU'],
    'Banks': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS'],
    'Retail': ['WMT', 'AMZN', 'COST', 'TGT', 'HD'],
    'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK'],
    'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB'],
    'Unknown': ['AAPL', 'GOOGL', 'AMZN', 'MSFT']
}


def get_peer_group(ticker: str, sector: str, custom_peers: List[str] = None) -> List[str]:
    """Получает список peer-компаний"""
    if custom_peers:
        return custom_peers
    
    peers = PEERS_BY_SECTOR.get(sector, PEERS_BY_SECTOR['Unknown'])
    peers = [p for p in peers if p != ticker]
    return peers[:5]


def calculate_peer_ratios(ticker: str, peers: List[str]) -> pd.DataFrame:
    """Рассчитывает мультипликаторы для peer-компаний"""
    results = []
    all_tickers = [ticker] + peers
    
    print(f"\n🔄 Анализируем {len(all_tickers)} компаний...")
    
    for i, t in enumerate(all_tickers):
        print(f"   {i+1}/{len(all_tickers)}: {t}...", end=" ")
        
        try:
            data = get_all_data(t)
            
            ratios = calculate_ratios(
                data['income_stmt'],
                data['balance_sheet'],
                data['cash_flow'],
                data['market_data']
            )
            
            result = {
                'Ticker': t,
                'Sector': data['market_data'].get('sector', 'Unknown'),
                'Price': data['market_data'].get('price', 0),
                'Market Cap (B)': data['market_data'].get('market_cap', 0) / 1e9,
            }
            result.update(ratios)
            results.append(result)
            print("✅")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            continue
    
    return pd.DataFrame(results)


def compare_with_peers(df: pd.DataFrame, main_ticker: str) -> Dict:
    """Сравнивает основную компанию с медианными значениями"""
    main_company = df[df['Ticker'] == main_ticker].iloc[0] if len(df[df['Ticker'] == main_ticker]) > 0 else None
    peers_df = df[df['Ticker'] != main_ticker]
    
    if main_company is None or peers_df.empty:
        return {'error': 'Недостаточно данных для сравнения'}
    
    metrics = ['P/E', 'P/B', 'EV/EBITDA', 'EV/Revenue', 'ROE (%)', 'ROA (%)', 'FCF Yield (%)']
    
    comparison = {
        'main_ticker': main_ticker,
        'peer_count': len(peers_df),
        'peers_list': peers_df['Ticker'].tolist(),
        'metrics': {}
    }
    
    for metric in metrics:
        if metric in main_company and metric in peers_df.columns:
            peer_values = peers_df[metric].dropna()
            if len(peer_values) > 0:
                median = peer_values.median()
                main_value = main_company[metric]
                
                if main_value and median > 0:
                    deviation_pct = ((main_value - median) / median) * 100
                else:
                    deviation_pct = 0
                
                if metric in ['P/E', 'P/B', 'EV/EBITDA', 'EV/Revenue']:
                    valuation = "дешевле" if main_value < median else "дороже"
                else:
                    valuation = "выше" if main_value > median else "ниже"
                
                comparison['metrics'][metric] = {
                    'company_value': round(main_value, 2) if main_value else None,
                    'industry_median': round(median, 2),
                    'deviation': round(deviation_pct, 1),
                    'valuation': f"{abs(round(deviation_pct, 1))}% {valuation} рынка"
                }
    
    return comparison
