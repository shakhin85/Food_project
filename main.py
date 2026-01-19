"""
Пример использования iiko SDK.
Демонстрирует основные возможности SDK для работы с iiko API.
"""

import logging

from src.iiko_sdk import IikoSDK

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def example_basic_usage():
    """Пример базового использования SDK."""
    print("\n" + "=" * 60)
    print("ПРИМЕР 1: Базовое использование")
    print("=" * 60 + "\n")

    # Создание SDK клиента
    sdk = IikoSDK()
    print(f"SDK создан: {sdk}")

    # Авторизация
    token = sdk.authenticate()
    print(f"Токен: {token[:30]}...")
    print(f"Статус: {sdk}")

    # Здесь можно выполнять запросы к API
    # Например:
    # response = sdk.get("/nomenclature")
    # print(response.text)

    # Выход
    sdk.logout()
    print(f"После выхода: {sdk}")


def example_context_manager():
    """Пример использования с context manager (рекомендуемый способ)."""
    print("\n" + "=" * 60)
    print("ПРИМЕР 2: Context Manager (рекомендуется)")
    print("=" * 60 + "\n")

    # Context manager автоматически выполнит logout
    with IikoSDK() as sdk:
        print(f"SDK: {sdk}")
        print(f"Токен: {sdk.token[:30] if sdk.token else 'None'}...")

        # Выполняем запросы
        # response = sdk.get("/nomenclature")

    print("Context manager автоматически выполнил logout")


def example_direct_auth_module():
    """Пример прямого использования модуля авторизации."""
    print("\n" + "=" * 60)
    print("ПРИМЕР 3: Прямое использование модуля авторизации")
    print("=" * 60 + "\n")

    from src.auth import AuthManager
    from src.client import HTTPClient
    from src.config import get_settings

    # Получаем настройки
    settings = get_settings()
    print(f"Base URL: {settings.rms_base_url}")

    # Создаем HTTP клиент
    http_client = HTTPClient(settings)

    # Создаем менеджер авторизации
    auth = AuthManager(settings, http_client)

    # Авторизация
    token = auth.authenticate()
    print(f"Токен получен: {token[:30]}...")

    # Проверка валидности токена
    is_valid = auth.validate_token()
    print(f"Токен валиден: {is_valid}")

    # Выход
    auth.logout()


def main():
    """Главная функция - запуск примеров."""
    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ iiko SDK")
    print("=" * 60)

    try:
        # Пример 1: Базовое использование
        example_basic_usage()

        # Пример 2: Context manager (рекомендуемый способ)
        example_context_manager()

        # Пример 3: Прямое использование модулей
        example_direct_auth_module()

        print("\n" + "=" * 60)
        print("Все примеры выполнены успешно!")
        print("=" * 60 + "\n")

        return 0

    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
