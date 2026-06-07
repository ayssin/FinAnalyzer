"""
Модуль скоринговой модели
Расчёт Z-score Альтмана
"""

import pandas as pd
from typing import Dict


def calculate_z_score(income_stmt: pd.DataFrame, 
                      balance_sheet: pd.DataFrame,
                      market_cap: float) -> Dict:
    """Рассчитывает Z-score Альтмана"""
    
    if income_stmt.empty or balance_sheet.empty:
        return {'z_score': None, 'zone': 'Нет данных', 'recommendation': 'Недостаточно данных для расчёта'}
    
    latest_income = income_stmt.iloc[0]
    latest_balance = balance_sheet.iloc[0]
    
    total_assets = latest_balance.get('Total Assets', 0)
    if total_assets == 0:
        return {'error': 'Нет данных об активах'}
    
    current_assets = latest_balance.get('Current Assets', 0)
    current_liabilities = latest_balance.get('Current Liabilities', 0)
    working_capital = current_assets - current_liabilities
    A = working_capital / total_assets
    
    retained_earnings = latest_balance.get('Retained Earnings', latest_balance.get('Total Equity', 0))
    B = retained_earnings / total_assets
    
    ebit = latest_income.get('EBIT', latest_income.get('Operating Income', 0))
    C = ebit / total_assets
    
    total_liabilities = latest_balance.get('Total Liabilities', 0)
    if total_liabilities == 0:
        total_debt = latest_balance.get('Total Debt', 0)
        total_liabilities = total_debt + current_liabilities
    
    if total_liabilities > 0 and market_cap > 0:
        D = market_cap / total_liabilities
    else:
        D = 1.0
    
    revenue = latest_income.get('Total Revenue', 0)
    E = revenue / total_assets
    
    z_score = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E
    
    if z_score > 3.0:
        zone = "Безопасная зона (низкий риск)"
        recommendation = "✅ Компания финансово устойчива"
    elif z_score >= 1.8:
        zone = "Серая зона (средний риск)"
        recommendation = "⚠️ Следите за финансовыми показателями"
    else:
        zone = "Зона риска (высокий риск)"
        recommendation = "❌ Компания требует детального анализа"
    
    return {
        'z_score': round(z_score, 2),
        'zone': zone,
        'recommendation': recommendation,
        'components': {
            'A (Working Capital/Assets)': round(A, 4),
            'B (Retained Earnings/Assets)': round(B, 4),
            'C (EBIT/Assets)': round(C, 4),
            'D (Market Cap/Liabilities)': round(D, 2),
            'E (Revenue/Assets)': round(E, 4)
        }
    }


def print_z_score(z_score_result: Dict):
    """Красиво выводит результат Z-score"""
    if not z_score_result or z_score_result.get('z_score') is None:
        print("\n⚠️ Z-score не рассчитан (нет данных)")
        return
    
    print("\n" + "="*50)
    print("🏦 Z-SCORE АЛЬТМАНА (Риск банкротства)")
    print("="*50)
    
    score = z_score_result['z_score']
    
    if score > 3.0:
        indicator = "🟢"
    elif score >= 1.8:
        indicator = "🟡"
    else:
        indicator = "🔴"
    
    print(f"\n{indicator} Z-Score: {score}")
    print(f"\n📌 {z_score_result['zone']}")
    print(f"💡 {z_score_result['recommendation']}")
    
    if 'components' in z_score_result:
        print("\n📐 Компоненты:")
        for key, value in z_score_result['components'].items():
            print(f"   {key:30} : {value}")
    
    print("\n📖 Шкала:")
    print("   🟢 > 3.0   - Безопасная зона")
    print("   🟡 1.8-3.0 - Серая зона")
    print("   🔴 < 1.8   - Зона риска")
    print("="*50)
