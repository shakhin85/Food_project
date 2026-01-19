"""
Пример использования OLAP-отчетов через SDK.
"""

import logging

from src.iiko_sdk import IikoSDK

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Тестирование OLAP методов."""
    print("\n" + "=" * 60)
    print("ТЕСТ: Получение колонок OLAP")
    print("=" * 60 + "\n")

    try:
        # Используем context manager для автоматического logout
        with IikoSDK() as sdk:
            # Получаем список колонок
            columns = sdk.olap.get_columns()

            print(f"Всего доступно колонок: {len(columns)}\n")

            # Выводим первые 10 колонок
            print("Первые 10 колонок:")
            print("-" * 60)
            for i, col in enumerate(columns[:10], 1):
                name = col.get("name", "N/A")
                caption = col.get("caption", "N/A")
                col_type = col.get("type", "N/A")
                print(f"{i}. {name}")
                print(f"   Caption: {caption}")
                print(f"   Type: {col_type}")
                print()

            # Выводим типы колонок
            print("\nТипы колонок:")
            print("-" * 60)
            types = {}
            for col in columns:
                col_type = col.get("type", "unknown")
                types[col_type] = types.get(col_type, 0) + 1

            for col_type, count in sorted(types.items()):
                print(f"  {col_type}: {count}")

            print("\n" + "=" * 60)
            print("✓ Тест завершен успешно!")
            print("=" * 60 + "\n")

            return 0

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
