"""
Простой пример работы с OLAP-отчетами.
"""

import pandas as pd

from src.iiko_sdk import IikoSDK

pd.options.display.width = 1000
pd.options.display.max_columns = 100


def main():
    """Пример получения колонок OLAP."""

    # Используем context manager для автоматического logout
    with IikoSDK() as sdk:
        # Получаем список доступных колонок для отчета SALES
        columns = sdk.olap.get_columns(report_type="SALES")

        print(f"Всего колонок: {len(columns)}\n")

        # Фильтруем колонки по типу MONEY (денежные показатели)
        money_columns = [col for col in columns if col.get("type") == "AMOUNT"]
        report_table = pd.DataFrame(money_columns)

        print("Денежные колонки:")
        for col in money_columns:
            print(f"  - {col['name']} (id: {col['id']})")

        print(f"\nВсего денежных колонок: {len(money_columns)}")


if __name__ == "__main__":
    main()
