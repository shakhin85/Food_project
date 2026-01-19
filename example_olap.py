"""
Простой пример работы с OLAP-отчетами.
"""

from src.iiko_sdk import IikoSDK


def main():
    """Пример получения колонок OLAP."""

    # Используем context manager для автоматического logout
    with IikoSDK() as sdk:

        # Получаем список доступных колонок для отчета SALES
        columns = sdk.olap.get_columns(report_type="SALES")

        print(f"Всего колонок: {len(columns)}\n")

        # Фильтруем колонки по типу MONEY (денежные показатели)
        money_columns = [col for col in columns if col.get("type") == "MONEY"]

        print("Денежные колонки:")
        for col in money_columns:
            print(f"  - {col['name']} (id: {col['id']})")

        print(f"\nВсего денежных колонок: {len(money_columns)}")


if __name__ == "__main__":
    main()
