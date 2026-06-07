"""
Модуль генерации отчётов с графиками, сентимент-анализом и ML прогнозом
"""

import json
import os
from datetime import datetime
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from finanalyzer.fetcher import get_all_data
from finanalyzer.ratios import calculate_ratios, print_ratios
from finanalyzer.scorer import calculate_z_score, print_z_score
from finanalyzer.peer_compare import get_peer_group, calculate_peer_ratios, compare_with_peers
from finanalyzer.sentiment_analyzer import get_stock_sentiment
from finanalyzer.ml_predictor import get_ml_forecast

CHARTS_DIR = "data/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def create_revenue_chart(income_stmt: pd.DataFrame, ticker: str) -> str:
    """Создаёт график динамики выручки и чистой прибыли (новые года слева)"""
    if income_stmt.empty:
        return None
    
    data = income_stmt.head(5).copy()
    data = data.iloc[::-1]  # Разворачиваем: новые года слева
    
    years = [d.strftime('%Y') if hasattr(d, 'strftime') else str(d) for d in data.index]
    
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    revenue_col = 'Total Revenue' if 'Total Revenue' in data.columns else 'Revenue'
    if revenue_col in data.columns:
        revenue = data[revenue_col] / 1e9
        ax1.bar(years, revenue, alpha=0.7, color='steelblue', label='Выручка')
        ax1.set_xlabel('Год')
        ax1.set_ylabel('Выручка (млрд $)', color='steelblue')
        ax1.tick_params(axis='y', labelcolor='steelblue')
    
    net_income_col = 'Net Income' if 'Net Income' in data.columns else 'NetIncome'
    if net_income_col in data.columns:
        net_income = data[net_income_col] / 1e9
        ax2 = ax1.twinx()
        ax2.plot(years, net_income, 'o-', color='coral', linewidth=2, markersize=8, label='Чистая прибыль')
        ax2.set_ylabel('Чистая прибыль (млрд $)', color='coral')
        ax2.tick_params(axis='y', labelcolor='coral')
    
    plt.title('Динамика выручки и прибыли', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    filename = f"{CHARTS_DIR}/{ticker}_revenue.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename


def create_roe_roa_chart(ratios: Dict, ticker: str) -> str:
    """Создаёт график рентабельности"""
    metrics = []
    values = []
    
    if 'ROE (%)' in ratios:
        metrics.append('ROE')
        values.append(ratios['ROE (%)'])
    if 'ROA (%)' in ratios:
        metrics.append('ROA')
        values.append(ratios['ROA (%)'])
    if 'FCF Yield (%)' in ratios:
        metrics.append('FCF Yield')
        values.append(ratios['FCF Yield (%)'])
    
    if not metrics:
        return None
    
    plt.figure(figsize=(8, 5))
    plt.bar(metrics, values, color=['steelblue', 'coral', 'seagreen'], alpha=0.7)
    plt.ylabel('%')
    plt.title('Показатели рентабельности', fontsize=14, fontweight='bold')
    plt.axhline(y=15, color='green', linestyle='--', alpha=0.5, label='Целевой уровень 15%')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    filename = f"{CHARTS_DIR}/{ticker}_roe_roa.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename


def create_sentiment_chart(sentiment: Dict, ticker: str) -> str:
    """Создаёт график сентимента новостей"""
    if sentiment['total_news'] == 0:
        return None
    
    labels = ['Позитивные', 'Негативные', 'Нейтральные']
    values = [sentiment['positive_count'], sentiment['negative_count'], sentiment['neutral_count']]
    colors_list = ['green', 'red', 'gray']
    
    plt.figure(figsize=(6, 4))
    plt.pie(values, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
    plt.title(f'Сентимент новостей (всего: {sentiment["total_news"]})', fontsize=12, fontweight='bold')
    plt.tight_layout()
    
    filename = f"{CHARTS_DIR}/{ticker}_sentiment.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename


def create_forecast_chart(forecast: Dict, ticker: str) -> str:
    """Создаёт график прогноза цены"""
    if 'error' in forecast:
        return None
    
    plt.figure(figsize=(8, 5))
    
    labels = ['Текущая', 'Прогноз']
    values = [forecast['current_price'], forecast['predicted_price']]
    colors_bar = ['steelblue', 'orange']
    
    bars = plt.bar(labels, values, color=colors_bar, alpha=0.7)
    plt.ylabel('Цена ($)')
    plt.title('ML Прогноз цены акции', fontsize=14, fontweight='bold')
    
    for bar, val in zip(bars, values):
        plt.annotate(f'${val:.2f}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                    xytext=(0, 5), textcoords="offset points", ha='center', va='bottom', fontsize=10)
    
    change = forecast['change_pct']
    color = 'green' if change > 0 else 'red'
    plt.text(0.5, max(values) * 0.9, f'Изменение: {change:+.1f}%', 
             ha='center', fontsize=12, color=color, fontweight='bold')
    
    plt.tight_layout()
    
    filename = f"{CHARTS_DIR}/{ticker}_forecast.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename


def generate_summary(ratios: Dict, z_score: Dict, sentiment: Dict, comparison: Dict = None, forecast: Dict = None) -> list:
    """Генерирует итоговое резюме"""
    summary = []
    
    score = z_score.get('z_score', 0)
    if score > 3:
        summary.append("Финансовое состояние: ХОРОШЕЕ")
    elif score > 1.8:
        summary.append("Финансовое состояние: УДОВЛЕТВОРИТЕЛЬНОЕ")
    else:
        summary.append("Финансовое состояние: ТРЕБУЕТ ВНИМАНИЯ")
    
    if 'P/E' in ratios:
        pe = ratios['P/E']
        if pe < 15:
            summary.append(f"P/E = {pe} — акции выглядят недооценёнными")
        elif pe > 25:
            summary.append(f"P/E = {pe} — акции могут быть переоценены")
        else:
            summary.append(f"P/E = {pe} — справедливая оценка")
    
    if 'ROE (%)' in ratios and ratios['ROE (%)'] > 15:
        summary.append(f"ROE = {ratios['ROE (%)']}% — высокая эффективность капитала")
    
    if sentiment['total_news'] > 0:
        if sentiment['overall_sentiment'] == 'ПОЗИТИВ':
            summary.append(f"Новостной фон: ПОЗИТИВНЫЙ ({sentiment['positive_pct']}% позитивных новостей)")
        elif sentiment['overall_sentiment'] == 'НЕГАТИВ':
            summary.append(f"Новостной фон: НЕГАТИВНЫЙ ({sentiment['negative_pct']}% негативных новостей)")
        else:
            summary.append(f"Новостной фон: НЕЙТРАЛЬНЫЙ")
    
    if comparison and 'metrics' in comparison:
        better_count = 0
        for metric, mdata in comparison['metrics'].items():
            if metric in ['ROE (%)', 'ROA (%)', 'FCF Yield (%)']:
                if mdata.get('company_value', 0) > mdata.get('industry_median', 0):
                    better_count += 1
            else:
                if mdata.get('company_value', 0) < mdata.get('industry_median', 0):
                    better_count += 1
        
        if better_count >= 3:
            summary.append(f"По {better_count} из {len(comparison['metrics'])} метрик компания превосходит конкурентов")
    
    if forecast and 'error' not in forecast:
        if forecast['change_pct'] > 2:
            summary.append(f"ML прогноз: ПОКУПАТЬ (прогнозируемый рост {forecast['change_pct']:+.1f}%)")
        elif forecast['change_pct'] > 0:
            summary.append(f"ML прогноз: ДЕРЖАТЬ (слабый рост {forecast['change_pct']:+.1f}%)")
        elif forecast['change_pct'] > -2:
            summary.append(f"ML прогноз: ДЕРЖАТЬ (слабое падение {forecast['change_pct']:+.1f}%)")
        else:
            summary.append(f"ML прогноз: ПРОДАВАТЬ (прогнозируемое падение {forecast['change_pct']:+.1f}%)")
    
    return summary


def generate_json_report(ticker: str, output_dir: str = "data/reports") -> str:
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nГенерация JSON отчёта для {ticker}...")
    
    data = get_all_data(ticker)
    ratios = calculate_ratios(data['income_stmt'], data['balance_sheet'], data['cash_flow'], data['market_data'])
    z_score = calculate_z_score(data['income_stmt'], data['balance_sheet'], data['market_data']['market_cap'])
    sentiment = get_stock_sentiment(ticker, 'us')
    forecast = get_ml_forecast(ticker)
    
    report = {
        'ticker': ticker,
        'analysis_date': datetime.now().isoformat(),
        'market_data': {
            'price': data['market_data'].get('price'),
            'market_cap': data['market_data'].get('market_cap'),
            'sector': data['market_data'].get('sector'),
        },
        'financial_ratios': ratios,
        'z_score': z_score.get('z_score'),
        'news_sentiment': {
            'total_news': sentiment['total_news'],
            'positive_pct': sentiment['positive_pct'],
            'negative_pct': sentiment['negative_pct'],
            'overall': sentiment['overall_sentiment']
        },
        'ml_forecast': {
            'predicted_price': forecast.get('predicted_price'),
            'change_pct': forecast.get('change_pct'),
            'recommendation': forecast.get('recommendation')
        } if 'error' not in forecast else None,
        'summary': generate_summary(ratios, z_score, sentiment, None, forecast if 'error' not in forecast else None)
    }
    
    filename = f"{output_dir}/{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"JSON отчёт сохранён: {filename}")
    return filename


def generate_pdf_report(ticker: str, output_dir: str = "data/reports") -> str:
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nГенерация PDF отчёта для {ticker}...")
    
    data = get_all_data(ticker)
    ratios = calculate_ratios(data['income_stmt'], data['balance_sheet'], data['cash_flow'], data['market_data'])
    z_score = calculate_z_score(data['income_stmt'], data['balance_sheet'], data['market_data']['market_cap'])
    sentiment = get_stock_sentiment(ticker, 'us')
    forecast = get_ml_forecast(ticker)
    
    sector = data['market_data'].get('sector', 'Technology')
    peers = get_peer_group(ticker, sector)
    peer_df = calculate_peer_ratios(ticker, peers)
    comparison = compare_with_peers(peer_df, ticker)
    
    print("   Создание графиков...")
    revenue_chart = create_revenue_chart(data['income_stmt'], ticker)
    roe_roa_chart = create_roe_roa_chart(ratios, ticker)
    sentiment_chart = create_sentiment_chart(sentiment, ticker) if sentiment['total_news'] > 0 else None
    forecast_chart = create_forecast_chart(forecast, ticker) if 'error' not in forecast else None
    
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
        FONT_NAME = 'Arial'
    except:
        FONT_NAME = 'Helvetica'
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RussianTitle', fontName=FONT_NAME, fontSize=24, textColor=colors.HexColor('#003366'), alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name='RussianHeading1', fontName=FONT_NAME, fontSize=14, textColor=colors.HexColor('#003366'), alignment=0, spaceAfter=10, spaceBefore=10))
    styles.add(ParagraphStyle(name='RussianNormal', fontName=FONT_NAME, fontSize=10, alignment=0, spaceAfter=5))
    styles.add(ParagraphStyle(name='RussianBold', fontName=FONT_NAME, fontSize=10, alignment=0, spaceAfter=5, textColor=colors.HexColor('#003366')))
    
    filename = f"{output_dir}/{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
                           leftMargin=15*mm, rightMargin=15*mm)
    
    story = []
    
    # Заголовок
    story.append(Paragraph(f"FinAnalyzer Отчёт", styles['RussianTitle']))
    story.append(Paragraph(ticker.upper(), ParagraphStyle('Company', parent=styles['RussianTitle'], fontSize=18)))
    story.append(Spacer(1, 10))
    
    # Информация о компании
    story.append(Paragraph("Информация о компании", styles['RussianHeading1']))
    company_data = [
        ["Тикер", ticker],
        ["Сектор", data['market_data'].get('sector', 'N/A')],
        ["Цена", f"${data['market_data'].get('price', 0):.2f}"],
        ["Капитализация", f"${data['market_data'].get('market_cap', 0)/1e9:.1f} млрд"],
    ]
    company_table = Table(company_data, colWidths=[60*mm, 100*mm])
    company_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 10),
                                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)]))
    story.append(company_table)
    story.append(Spacer(1, 10))
    
    # График выручки
    if revenue_chart and os.path.exists(revenue_chart):
        story.append(Paragraph("Динамика выручки и прибыли", styles['RussianHeading1']))
        story.append(Image(revenue_chart, width=170*mm, height=80*mm))
        story.append(Spacer(1, 10))
    
    # Финансовые мультипликаторы
    story.append(Paragraph("Финансовые мультипликаторы", styles['RussianHeading1']))
    ratio_data = [["Показатель", "Значение"]]
    for m in ['P/E', 'P/B', 'EV/EBITDA', 'ROE (%)', 'ROA (%)', 'FCF Yield (%)']:
        if m in ratios:
            ratio_data.append([m, str(ratios[m])])
    
    ratio_table = Table(ratio_data, colWidths=[60*mm, 100*mm])
    ratio_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 10),
                                      ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                      ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue)]))
    story.append(ratio_table)
    story.append(Spacer(1, 10))
    
    # Сравнение с конкурентами
    if comparison and 'metrics' in comparison:
        story.append(Paragraph("Сравнение с конкурентами", styles['RussianHeading1']))
        
        comp_data = [["Показатель", "Значение", "Медиана", "Отклонение"]]
        for metric, mdata in comparison['metrics'].items():
            comp_data.append([
                metric,
                str(mdata.get('company_value', 'Н/Д')),
                str(mdata.get('industry_median', 'Н/Д')),
                mdata.get('valuation', '')
            ])
        
        comp_table = Table(comp_data, colWidths=[45*mm, 40*mm, 40*mm, 55*mm])
        comp_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 8),
                                         ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                         ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue)]))
        story.append(comp_table)
        story.append(Spacer(1, 10))
    
    # График рентабельности
    if roe_roa_chart and os.path.exists(roe_roa_chart):
        story.append(Paragraph("Показатели рентабельности", styles['RussianHeading1']))
        story.append(Image(roe_roa_chart, width=140*mm, height=70*mm))
        story.append(Spacer(1, 10))
    
    # Z-Score
    story.append(Paragraph("Z-Score Альтмана", styles['RussianHeading1']))
    score = z_score.get('z_score', 0)
    if score > 3:
        risk = "Низкий риск"
        color = colors.green
    elif score > 1.8:
        risk = "Средний риск"
        color = colors.orange
    else:
        risk = "Высокий риск"
        color = colors.red
    
    story.append(Paragraph(f"Z-Score: {score} - {risk}", ParagraphStyle('ZScore', parent=styles['RussianNormal'], fontSize=12, textColor=color)))
    story.append(Spacer(1, 10))
    
    # Новостной сентимент
    if sentiment['total_news'] > 0:
        story.append(Paragraph("Новостной сентимент", styles['RussianHeading1']))
        
        sentiment_data = [
            ["Новостей", str(sentiment['total_news'])],
            ["Позитивные", f"{sentiment['positive_count']} ({sentiment['positive_pct']}%)"],
            ["Негативные", f"{sentiment['negative_count']} ({sentiment['negative_pct']}%)"],
            ["Общая оценка", sentiment['overall_sentiment']],
        ]
        sent_table = Table(sentiment_data, colWidths=[60*mm, 100*mm])
        sent_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 10),
                                         ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                         ('BACKGROUND', (0, 0), (0, -1), colors.lavender)]))
        story.append(sent_table)
        story.append(Spacer(1, 10))
        
        if sentiment_chart and os.path.exists(sentiment_chart):
            story.append(Image(sentiment_chart, width=100*mm, height=80*mm))
            story.append(Spacer(1, 10))
        
        if sentiment.get('news_items'):
            story.append(Paragraph("Последние новости", styles['RussianHeading1']))
            for item in sentiment['news_items'][:3]:
                headline = item['headline'][:80] + "..." if len(item['headline']) > 80 else item['headline']
                story.append(Paragraph(f"• {headline} [{item['sentiment']}]", styles['RussianNormal']))
            story.append(Spacer(1, 10))
    
    # ML Прогноз
    if 'error' not in forecast:
        story.append(Paragraph("ML Прогноз цены", styles['RussianHeading1']))
        
        forecast_data = [
            ["Текущая цена", f"${forecast['current_price']:.2f}"],
            ["Прогноз на завтра", f"${forecast['predicted_price']:.2f}"],
            ["Изменение", f"{forecast['change_pct']:+.1f}% (${forecast['change_abs']:+.2f})"],
            ["Доверительный интервал", f"${forecast['confidence_interval']['lower']} - ${forecast['confidence_interval']['upper']}"],
            ["Рекомендация", forecast['recommendation']],
            ["Качество модели (R²)", str(forecast['model_quality']['r2_score'])],
            ["Точность направления", f"{forecast['model_quality']['accuracy']}%"],
        ]
        
        forecast_table = Table(forecast_data, colWidths=[60*mm, 100*mm])
        forecast_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 10),
                                             ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                             ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen)]))
        story.append(forecast_table)
        story.append(Spacer(1, 10))
        
        if forecast_chart and os.path.exists(forecast_chart):
            story.append(Image(forecast_chart, width=120*mm, height=70*mm))
            story.append(Spacer(1, 10))
    
    # Итоговое резюме
    story.append(Paragraph("Итоговое резюме", styles['RussianHeading1']))
    for item in generate_summary(ratios, z_score, sentiment, comparison, forecast if 'error' not in forecast else None):
        story.append(Paragraph(f"✓ {item}", styles['RussianBold']))
    
    doc.build(story)
    
    for chart in [revenue_chart, roe_roa_chart, sentiment_chart, forecast_chart]:
        if chart and os.path.exists(chart):
            try:
                os.remove(chart)
            except:
                pass
    
    print(f"PDF отчёт сохранён: {filename}")
    return filename


def полный_анализ(ticker: str, save_json: bool = True, save_pdf: bool = True):
    """Запускает полный анализ компании"""
    print(f"\nЗАПУСК ПОЛНОГО АНАЛИЗА ДЛЯ {ticker.upper()}")
    print("="*60)
    
    data = get_all_data(ticker)
    ratios = calculate_ratios(data['income_stmt'], data['balance_sheet'], data['cash_flow'], data['market_data'])
    z_score = calculate_z_score(data['income_stmt'], data['balance_sheet'], data['market_data']['market_cap'])
    sentiment = get_stock_sentiment(ticker, 'us')
    sector = data['market_data'].get('sector', 'Technology')
    peers = get_peer_group(ticker, sector)
    peer_df = calculate_peer_ratios(ticker, peers)
    comparison = compare_with_peers(peer_df, ticker)
    
    print_ratios(ratios)
    print_z_score(z_score)
    
    print(f"\n📰 НОВОСТНОЙ СЕНТИМЕНТ:")
    print(f"   Анализировано новостей: {sentiment['total_news']}")
    print(f"   Позитивные: {sentiment['positive_count']} ({sentiment['positive_pct']}%)")
    print(f"   Негативные: {sentiment['negative_count']} ({sentiment['negative_pct']}%)")
    print(f"   Общая оценка: {sentiment['overall_sentiment']}")
    
    if comparison and 'metrics' in comparison:
        print(f"\n👥 СРАВНЕНИЕ С КОНКУРЕНТАМИ:")
        for metric, mdata in comparison['metrics'].items():
            print(f"   {metric}: {mdata.get('valuation', 'Н/Д')}")
    
    print(f"\n🤖 ML ПРОГНОЗ НА ЗАВТРА:")
    print(f"{'='*50}")
    
    try:
        forecast = get_ml_forecast(ticker)
        if 'error' in forecast:
            print(f"   ⚠️ {forecast['error']}")
        else:
            print(f"   Текущая цена: ${forecast['current_price']}")
            print(f"   Прогноз: ${forecast['predicted_price']}")
            print(f"   Изменение: {forecast['change_pct']:+.1f}% (${forecast['change_abs']:+.2f})")
            print(f"   {forecast['signal']} Рекомендация: {forecast['recommendation']}")
            print(f"\n   📊 Качество модели:")
            print(f"      R²: {forecast['model_quality']['r2_score']}")
            print(f"      Точность направления: {forecast['model_quality']['accuracy']}%")
    except Exception as e:
        print(f"   ⚠️ Ошибка ML прогноза: {e}")
    
    print(f"\n💡 ИТОГОВОЕ РЕЗЮМЕ:")
    for item in generate_summary(ratios, z_score, sentiment, comparison, forecast if 'error' not in forecast else None):
        print(f"   {item}")
    
    if save_json:
        generate_json_report(ticker)
    if save_pdf:
        generate_pdf_report(ticker)
    
    print(f"\nАнализ для {ticker} завершён!")


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "MSFT"
    полный_анализ(ticker, save_json=True, save_pdf=True)
