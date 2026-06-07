"""
Модуль расчёта финансовых мультипликаторов
"""

import pandas as pd
from typing import Dict


def calculate_ratios(income_stmt: pd.DataFrame, 
                     balance_sheet: pd.DataFrame, 
                     cash_flow: pd.DataFrame,
                     market_data: Dict) -> Dict:
    """Рассчитывает все основные мультипликаторы"""
    ratios = {}
    
    # Проверяем, что данные не пустые
    if income_stmt.empty or balance_sheet.empty:
        return ratios
    
    latest_income = income_stmt.iloc[0]
    latest_balance = balance_sheet.iloc[0]
    
    # Проверяем cash_flow на пустоту
    if cash_flow is not None and not cash_flow.empty:
        latest_cashflow = cash_flow.iloc[0]
    else:
        latest_cashflow = None
    
    market_cap = market_data.get('market_cap', 0)
    
    # P/E
    net_income = latest_income.get('Net Income', 0)
    if net_income and net_income > 0:
        ratios['P/E'] = round(market_cap / net_income, 2)
    
    # P/B
    total_equity = latest_balance.get('Total Equity', 0)
    if total_equity and total_equity > 0:
        ratios['P/B'] = round(market_cap / total_equity, 2)
    
    # EV/EBITDA
    total_debt = latest_balance.get('Total Debt', 0)
    cash = latest_balance.get('Cash And Cash Equivalents', 0)
    ev = market_cap + total_debt - cash
    
    ebit = latest_income.get('EBIT', latest_income.get('Operating Income', 0))
    
    # Получаем Depreciation если есть
    depreciation = 0
    if latest_cashflow is not None:
        if 'Depreciation' in latest_cashflow.index:
            depreciation = latest_cashflow.get('Depreciation', 0)
        elif 'Depreciation & Amortization' in latest_cashflow.index:
            depreciation = latest_cashflow.get('Depreciation & Amortization', 0)
    
    ebitda = ebit + depreciation
    
    if ebitda and ebitda > 0:
        ratios['EV/EBITDA'] = round(ev / ebitda, 2)
        ratios['EV'] = ev
        ratios['EBITDA'] = ebitda
    
    # EV/Revenue
    revenue = latest_income.get('Total Revenue', 0)
    if revenue > 0:
        ratios['EV/Revenue'] = round(ev / revenue, 2)
    
    # ROE
    if net_income and total_equity and total_equity > 0:
        ratios['ROE (%)'] = round((net_income / total_equity) * 100, 2)
    
    # ROA
    total_assets = latest_balance.get('Total Assets', 0)
    if net_income and total_assets and total_assets > 0:
        ratios['ROA (%)'] = round((net_income / total_assets) * 100, 2)
    
    # Current Ratio
    current_assets = latest_balance.get('Current Assets', 0)
    current_liabilities = latest_balance.get('Current Liabilities', 0)
    if current_liabilities and current_liabilities > 0:
        ratios['Current Ratio'] = round(current_assets / current_liabilities, 2)
    
    # FCF Yield
    if latest_cashflow is not None:
        fcf = latest_cashflow.get('Free Cash Flow', 0)
        if fcf and market_cap > 0:
            ratios['FCF Yield (%)'] = round((fcf / market_cap) * 100, 2)
    
    return ratios


def print_ratios(ratios: Dict):
    """Красиво выводит мультипликаторы"""
    if not ratios:
        print("\n⚠️ Нет данных для расчёта мультипликаторов")
        return
    
    print("\n" + "="*50)
    print("📊 ФИНАНСОВЫЕ МУЛЬТИПЛИКАТОРЫ")
    print("="*50)
    
    for key, value in ratios.items():
        if key in ['EV', 'EBITDA'] and isinstance(value, (int, float)):
            if value > 1e9:
                print(f"{key:20} : ${value/1e9:.2f} млрд")
            elif value > 1e6:
                print(f"{key:20} : ${value/1e6:.2f} млн")
            else:
                print(f"{key:20} : ${value:,.0f}")
        else:
            print(f"{key:20} : {value}")
    
    print("="*50)
