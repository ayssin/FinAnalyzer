# FinAnalyzer

Инструмент для анализа акций. Сам собирает данные, считает мультипликаторы, мониторит новости и пытается предсказать цену.

Работает с США и Россией.

---

## Что умеет

- Загружает отчётность (выручка, долги, денежный поток)
- Считает P/E, P/B, EV/EBITDA, ROE, ROA, FCF Yield
- Оценивает риск банкротства (Z-score Альтмана)
- Сравнивает с конкурентами
- Парсит новости из RSS, определяет тональность
- Прогнозирует цену на завтра (Random Forest)
- Делает PDF-отчёт с графиками

---

## Установка

```bash
git clone https://github.com/ayssin/FinAnalyzer.git
cd FinAnalyzer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Запуск

### Американские акции
```bash
python -m finanalyzer.report MSFT
python -m finanalyzer.report AAPL
python -m finanalyzer.report NVDA
```

### Российские акции
```bash
python -m finanalyzer.russia_report SBER
python -m finanalyzer.russia_report GAZP
```

### Отдельно ML прогноз
```bash
python -m finanalyzer.ml_predictor
```

### Отдельно сентимент новостей
```bash
python -m finanalyzer.sentiment_analyzer
```

---

## Что получается на выходе

После запуска в папке `data/reports/` появляются два файла:
- `MSFT_20260607_185420.pdf` — отчёт с графиками
- `MSFT_20260607_185420.json` — данные в формате JSON

---

## Пример вывода в консоль для MSFT

```
📊 ФИНАНСОВЫЕ МУЛЬТИПЛИКАТОРЫ
P/E                  : 30.4
EV/EBITDA            : 19.51
ROE (%)              : 36.78%

🏦 Z-SCORE АЛЬТМАНА
Z-Score: 10.96 - Низкий риск

📰 НОВОСТНОЙ СЕНТИМЕНТ
Новостей: 20 | Позитив: 45% | Общая оценка: ПОЗИТИВ

🤖 ML ПРОГНОЗ НА ЗАВТРА
Текущая: $416.67 → Прогноз: $421.25 (+1.1%)
Рекомендация: ДЕРЖАТЬ
```

---

## Структура проекта

```
FinAnalyzer/
├── finanalyzer/
│   ├── fetcher.py
│   ├── ratios.py
│   ├── scorer.py
│   ├── peer_compare.py
│   ├── sentiment_analyzer.py
│   ├── ml_predictor.py
│   ├── report.py
│   └── russia_report.py
├── data/
│   ├── reports/
│   └── charts/
├── requirements.txt
└── README.md
```

---

## Откуда данные

- **США:** Yahoo Finance (котировки, отчётность, новости)
- **Россия:** MOEX API (котировки), RSS ленты (новости)

---

## ML модель

- Алгоритм: Random Forest
- Признаки: лаги цены, скользящие средние, RSI, волатильность
- R² = 0.91, средняя ошибка = $5

---

## Лицензия

MIT