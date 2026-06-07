from finanalyzer.fetcher import get_all_data

ticker = "MSFT"
data = get_all_data(ticker)

print("\n=== КОЛОНКИ В ОТЧЁТЕ О ПРИБЫЛЯХ ===")
print(data["income_stmt"].columns.tolist())

print("\n=== ПЕРВАЯ СТРОКА ОТЧЁТА О ПРИБЫЛЯХ ===")
print(data["income_stmt"].iloc[0])

print("\n=== КОЛОНКИ В БАЛАНСЕ ===")
print(data["balance_sheet"].columns.tolist())

print("\n=== ПЕРВАЯ СТРОКА БАЛАНСА ===")
print(data["balance_sheet"].iloc[0])

print("\n=== КОЛОНКИ В ДЕНЕЖНОМ ПОТОКЕ ===")
print(data["cash_flow"].columns.tolist())
