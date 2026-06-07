# \# 📊 FinAnalyzer

# 

# <p align="center">

# &#x20; <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge\&logo=python\&logoColor=white"/>

# &#x20; <img src="https://img.shields.io/badge/ML-RandomForest-orange?style=for-the-badge\&logo=scikit-learn\&logoColor=white"/>

# &#x20; <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>

# </p>

# 

# \*\*Автоматизированный инструмент для фундаментального анализа акций\*\*

# 

# \## 🚀 Возможности

# 

# | Функция | Описание |

# |---------|----------|

# | 📈 \*\*Мультипликаторы\*\* | P/E, P/B, EV/EBITDA, ROE, ROA, FCF Yield |

# | 🏦 \*\*Z-Score Альтмана\*\* | Оценка риска банкротства |

# | 👥 \*\*Peer Compare\*\* | Сравнение с конкурентами |

# | 📰 \*\*Сентимент новостей\*\* | Анализ тональности (US + RU) |

# | 🤖 \*\*ML прогноз\*\* | Предсказание цены на завтра |

# | 📄 \*\*PDF отчёт\*\* | Профессиональный отчёт с графиками |

# | 🇷🇺 \*\*Российский рынок\*\* | Поддержка MOEX |

# 

# \## 📦 Установка

# 

# ```bash

# git clone https://github.com/ayssin/FinAnalyzer.git

# cd FinAnalyzer

# python -m venv venv

# venv\\Scripts\\activate

# pip install -r requirements.txt

# ```

# 

# \## 🎯 Использование

# 

# ```bash

# \# Американские акции

# python -m finanalyzer.report MSFT

# python -m finanalyzer.report AAPL

# 

# \# Российские акции

# python -m finanalyzer.russia\_report SBER

# python -m finanalyzer.russia\_report GAZP

# 

# \# ML прогноз

# python -m finanalyzer.ml\_predictor

# ```

# 

# \## 📊 Пример вывода

# 

# ```

# 📊 ФИНАНСОВЫЕ МУЛЬТИПЛИКАТОРЫ

# P/E: 30.4 | ROE: 36.78% | FCF Yield: 2.31%

# 

# 🤖 ML ПРОГНОЗ: $421.25 (+1.1%)

# Рекомендация: ДЕРЖАТЬ

# ```

# 

# \## 📁 Структура

# 

# ```

# FinAnalyzer/

# ├── finanalyzer/       # Основной код

# ├── data/reports/      # PDF и JSON отчёты

# └── README.md

# ```

# 

# \## 📄 Лицензия

# 

# MIT License

# 

# ⭐ Если полезно — поставь звезду!

