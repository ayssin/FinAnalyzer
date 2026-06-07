"""
Модуль анализа российских акций
Работает через MOEX API + yfinance, включает графики и сравнение с конкурентами
"""

import json
import os
from datetime import datetime
import tempfile

import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from finanalyzer.russia_fetcher import get_russian_stock_data, RussiaStockFetcher


def create_price_chart(ticker: str) -> str:
    """Создаёт график цены акции"""
    fetcher = RussiaStockFetcher()
    prices = fetcher.get_historical_prices(ticker)
    
    if not prices:
        return None
    
    prices = prices[:180]
    dates = [p[0] for p in prices]
    values = [p[1] for p in prices]
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, 'b-', linewidth=1.5, label='Цена')
    plt.fill_between(range(len(values)), values, alpha=0.3)
    
    if len(values) > 20:
        ma20 = [sum(values[i:i+20])/20 for i in range(len(values)-19)]
        plt.plot(range(19, len(values)), ma20, 'r--', linewidth=1, label='MA20')
    
    plt.xlabel('Дата')
    plt.ylabel('Цена (RUB)')
    plt.title(f'Динамика цены {ticker}', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
    plt.close()
    
    return temp_file.name


def create_comparison_table(ticker: str, data: dict) -> list:
    """Создаёт таблицу сравнения с конкурентами"""
    competitors = data.get('competitors', [])
    
    if not competitors:
        return None
    
    table_data = [['Компания', 'P/E', 'P/B', 'ROE%']]
    
    # Добавляем текущую компанию
    table_data.append([
        f"{data.get('shortname', ticker)} (основная)",
        f"{data.get('p_e', 'Н/Д'):.2f}" if data.get('p_e') else 'Н/Д',
        f"{data.get('p_b', 'Н/Д'):.2f}" if data.get('p_b') else 'Н/Д',
        f"{data.get('roe', 'Н/Д'):.1f}" if data.get('roe') else 'Н/Д',
    ])
    
    # Добавляем конкурентов
    for comp in competitors:
        table_data.append([
            comp.get('name', comp.get('ticker')),
            f"{comp.get('p_e', 'Н/Д'):.2f}" if comp.get('p_e') else 'Н/Д',
            f"{comp.get('p_b', 'Н/Д'):.2f}" if comp.get('p_b') else 'Н/Д',
            f"{comp.get('roe', 'Н/Д'):.1f}" if comp.get('roe') else 'Н/Д',
        ])
    
    return table_data


def get_pe_benchmark(pe: float) -> tuple:
    if pe < 5:
        return ("Сильно недооценена", colors.green)
    elif pe < 10:
        return ("Недооценена", colors.lightgreen)
    elif pe < 15:
        return ("Справедливая оценка", colors.orange)
    elif pe < 25:
        return ("Переоценена", colors.orangered)
    else:
        return ("Сильно переоценена", colors.red)


def get_roe_benchmark(roe: float) -> tuple:
    if roe > 20:
        return ("Отличная", colors.green)
    elif roe > 15:
        return ("Хорошая", colors.lightgreen)
    elif roe > 10:
        return ("Средняя", colors.orange)
    else:
        return ("Низкая", colors.red)


def generate_summary(data: dict) -> list:
    summary = []
    
    pe = data.get('p_e')
    pb = data.get('p_b')
    roe = data.get('roe')
    
    if pe:
        pe_text, _ = get_pe_benchmark(pe)
        summary.append(f"P/E = {pe:.2f} — {pe_text}")
    
    if pb and pb < 1:
        summary.append(f"P/B = {pb:.2f} — Акции торгуются ниже балансовой стоимости")
    
    if roe:
        roe_text, _ = get_roe_benchmark(roe)
        summary.append(f"ROE = {roe:.2f}% — {roe_text} рентабельность")
    
    return summary


def создать_json_отчёт(тикер: str, папка_вывода: str = "data/reports") -> str:
    os.makedirs(папка_вывода, exist_ok=True)
    
    данные = get_russian_stock_data(тикер)
    
    отчёт = {
        'тикер': тикер,
        'дата_анализа': datetime.now().isoformat(),
        'рыночные_данные': {
            'цена': данные.get('price'),
            'компания': данные.get('company_name'),
            'сектор': данные.get('sector'),
            'биржа': данные.get('exchange'),
        },
        'мультипликаторы': {
            'p_e': данные.get('p_e'),
            'p_b': данные.get('p_b'),
            'roe': данные.get('roe'),
            'eps': данные.get('eps'),
        },
        'конкуренты': данные.get('competitors', []),
        'резюме': generate_summary(данные)
    }
    
    имя_файла = f"{папка_вывода}/{тикер}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(имя_файла, 'w', encoding='utf-8') as f:
        json.dump(отчёт, f, indent=2, ensure_ascii=False)
    
    print(f"JSON отчёт сохранён: {имя_файла}")
    return имя_файла


def создать_pdf_отчёт(тикер: str, папка_вывода: str = "data/reports") -> str:
    os.makedirs(папка_вывода, exist_ok=True)
    
    print(f"\nГенерация PDF отчёта для {тикер}...")
    
    данные = get_russian_stock_data(тикер)
    
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
        FONT_NAME = 'Arial'
    except:
        FONT_NAME = 'Helvetica'
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RussianTitle', fontName=FONT_NAME, fontSize=24,
                              textColor=colors.HexColor('#003366'), alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name='RussianHeading1', fontName=FONT_NAME, fontSize=14,
                              textColor=colors.HexColor('#003366'), alignment=0, spaceAfter=10, spaceBefore=10))
    styles.add(ParagraphStyle(name='RussianNormal', fontName=FONT_NAME, fontSize=10, alignment=0, spaceAfter=5))
    styles.add(ParagraphStyle(name='RussianBold', fontName=FONT_NAME, fontSize=11, alignment=0,
                              spaceAfter=5, textColor=colors.HexColor('#003366')))
    
    имя_файла = f"{папка_вывода}/{тикер}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(имя_файла, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
                           leftMargin=15*mm, rightMargin=15*mm)
    
    story = []
    
    # Заголовок
    story.append(Paragraph(f"FinAnalyzer Отчёт - {тикер}", styles['RussianTitle']))
    story.append(Spacer(1, 10))
    
    # Информация о компании
    story.append(Paragraph("Информация о компании", styles['RussianHeading1']))
    данные_компании = [
        ["Тикер", тикер],
        ["Компания", данные.get('company_name', 'Н/Д')],
        ["Сектор", данные.get('sector', 'Н/Д')],
        ["Биржа", данные.get('exchange', 'Н/Д')],
        ["Валюта", данные.get('currency', 'Н/Д')],
    ]
    таблица = Table(данные_компании, colWidths=[60*mm, 100*mm])
    таблица.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 10),
                                  ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                  ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)]))
    story.append(таблица)
    story.append(Spacer(1, 15))
    
    # График цены
    print("  Создание графика цены...")
    chart_path = create_price_chart(тикер)
    if chart_path:
        story.append(Paragraph("Динамика цены акции", styles['RussianHeading1']))
        story.append(Image(chart_path, width=170*mm, height=80*mm))
        story.append(Spacer(1, 10))
        try:
            os.unlink(chart_path)
        except:
            pass
    
    # Мультипликаторы
    story.append(Paragraph("Финансовые мультипликаторы", styles['RussianHeading1']))
    мультипликаторы = [
        ["P/E", f"{данные.get('p_e', 'Н/Д'):.2f}" if данные.get('p_e') else 'Н/Д'],
        ["P/B", f"{данные.get('p_b', 'Н/Д'):.2f}" if данные.get('p_b') else 'Н/Д'],
        ["ROE", f"{данные.get('roe', 'Н/Д'):.2f}%" if данные.get('roe') else 'Н/Д'],
        ["EPS", f"{данные.get('eps', 'Н/Д'):.2f}" if данные.get('eps') else 'Н/Д'],
        ["Цена", f"{данные.get('price', 0):.2f} RUB"],
    ]
    таблица3 = Table(мультипликаторы, colWidths=[60*mm, 100*mm])
    таблица3.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 10),
                                   ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                   ('BACKGROUND', (0, 0), (0, -1), colors.lightblue)]))
    story.append(таблица3)
    story.append(Spacer(1, 15))
    
    # Сравнение с конкурентами
    story.append(Paragraph("Сравнение с конкурентами", styles['RussianHeading1']))
    comparison_table = create_comparison_table(тикер, данные)
    if comparison_table:
        comp_table = Table(comparison_table, colWidths=[60*mm, 40*mm, 40*mm, 40*mm])
        comp_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), FONT_NAME), ('FONTSIZE', (0, 0), (-1, -1), 9),
                                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue)]))
        story.append(comp_table)
    else:
        story.append(Paragraph("Нет данных для сравнения", styles['RussianNormal']))
    story.append(Spacer(1, 15))
    
    # Анализ и резюме
    story.append(Paragraph("Анализ мультипликаторов", styles['RussianHeading1']))
    pe = данные.get('p_e')
    if pe:
        pe_text, pe_color = get_pe_benchmark(pe)
        story.append(Paragraph(f"• P/E = {pe:.2f} — {pe_text}", styles['RussianNormal']))
    pb = данные.get('p_b')
    if pb and pb < 1:
        story.append(Paragraph(f"• P/B = {pb:.2f} — Акции торгуются ниже балансовой стоимости", styles['RussianNormal']))
    roe = данные.get('roe')
    if roe:
        roe_text, _ = get_roe_benchmark(roe)
        story.append(Paragraph(f"• ROE = {roe:.2f}% — {roe_text} рентабельность", styles['RussianNormal']))
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("Итоговое резюме", styles['RussianHeading1']))
    for item in generate_summary(данные):
        story.append(Paragraph(f"  ✓ {item}", styles['RussianBold']))
    
    if pe and pe < 5 and pb and pb < 1:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Рекомендация: АКЦИИ СИЛЬНО НЕДООЦЕНЕНЫ",
                              ParagraphStyle('Recommendation', parent=styles['RussianBold'],
                                            fontSize=12, textColor=colors.green)))
    
    doc.build(story)
    print(f"PDF отчёт сохранён: {имя_файла}")
    return имя_файла


def полный_анализ(тикер: str, сохранить_json: bool = True, сохранить_pdf: bool = True):
    print(f"\nЗАПУСК АНАЛИЗА ДЛЯ РОССИЙСКОЙ АКЦИИ {тикер.upper()}")
    print("="*60)
    
    данные = get_russian_stock_data(тикер)
    
    print(f"\n📊 Данные для {тикер}:")
    print(f"   Компания: {данные.get('company_name', 'Н/Д')}")
    print(f"   Цена: {данные.get('price', 0)} RUB")
    print(f"\n📈 Мультипликаторы:")
    print(f"   P/E: {данные.get('p_e', 'Н/Д')}")
    print(f"   P/B: {данные.get('p_b', 'Н/Д')}")
    print(f"   ROE: {данные.get('roe', 'Н/Д')}%")
    
    if данные.get('competitors'):
        print(f"\n👥 Конкуренты:")
        for comp in данные.get('competitors', []):
            print(f"   {comp.get('name')}: P/E={comp.get('p_e', 'Н/Д')}")
    
    print(f"\n💡 Резюме:")
    for line in generate_summary(данные):
        print(f"   {line}")
    
    if сохранить_json:
        создать_json_отчёт(тикер)
    if сохранить_pdf:
        создать_pdf_отчёт(тикер)
    
    print(f"\nАнализ для {тикер} завершён!")


if __name__ == "__main__":
    import sys
    тикер = sys.argv[1].upper() if len(sys.argv) > 1 else "SBER"
    полный_анализ(тикер, сохранить_json=True, сохранить_pdf=True)
