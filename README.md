# iiko API SDK

Python SDK для работы с [API iiko](https://ru.iiko.help/articles/api-documentations/iikoserver-api).

## Описание

Модульный Python SDK для работы с iiko API, построенный на принципах ООП. Предоставляет удобный интерфейс для авторизации и выполнения запросов к iiko API.

### Основные возможности

- Автоматическое управление авторизацией и токенами
- Сохранение токена между запусками приложения
- Соблюдение рекомендаций iiko API (последовательные запросы)
- Автоматические повторные попытки при ошибках
- Поддержка различных типов контента (form-data, XML)
- Логирование всех операций
- Context manager для автоматического освобождения лицензии

## Структура проекта

```
.
├── src/
│   ├── __init__.py              # Главный экспорт SDK
│   ├── iiko_sdk.py              # Главный SDK клиент
│   ├── auth/                    # Модуль авторизации
│   │   ├── __init__.py
│   │   └── auth_manager.py      # Управление токенами
│   ├── client/                  # HTTP клиент
│   │   ├── __init__.py
│   │   └── http_client.py       # Базовый HTTP клиент
│   ├── config/                  # Конфигурация
│   │   ├── __init__.py
│   │   └── settings.py          # Настройки приложения
│   ├── models/                  # Модели данных
│   │   └── __init__.py
│   └── utils/                   # Утилиты
│       └── __init__.py
├── main.py                      # Примеры использования
├── .env                         # Переменные окружения
├── pyproject.toml               # Зависимости проекта
└── README.md                    # Документация
```

## Установка

### Требования

- Python 3.12+
- uv (менеджер пакетов)

### Установка зависимостей

```bash
uv sync
```

## Конфигурация

Создайте файл `.env` в корне проекта со следующими переменными:

```env
rms_base_url=https://your-server.iiko.it:443/resto/api
rms_login=your_login
rms_password=your_password
```

### Дополнительные параметры (опционально)

```env
# Путь для хранения токена (по умолчанию: .token)
token_storage_path=.token

# Таймаут для HTTP запросов в секундах (по умолчанию: 30)
request_timeout=30

# Максимальное количество повторных попыток (по умолчанию: 3)
max_retries=3
```

## Использование

### Пример 1: Базовое использование

```python
from src import IikoSDK

# Создание SDK клиента
sdk = IikoSDK()

# Авторизация
token = sdk.authenticate()
print(f"Токен: {token}")

# Выполнение запросов
response = sdk.get("/nomenclature")
print(response.text)

# Выход (освобождение лицензии)
sdk.logout()
```

### Пример 2: Context Manager (рекомендуется)

```python
from src import IikoSDK

# Context manager автоматически выполнит logout
with IikoSDK() as sdk:
    # Авторизация выполняется автоматически
    response = sdk.get("/nomenclature")
    print(response.text)

# Лицензия автоматически освобождена
```

### Пример 3: Прямое использование модулей

```python
from src.config import get_settings
from src.client import HTTPClient
from src.auth import AuthManager

# Получение настроек
settings = get_settings()

# Создание HTTP клиента
http_client = HTTPClient(settings)

# Создание менеджера авторизации
auth = AuthManager(settings, http_client)

# Авторизация
token = auth.authenticate()

# Проверка валидности токена
if auth.validate_token():
    print("Токен валиден")

# Выход
auth.logout()
```

## API Reference

### IikoSDK

Главный класс SDK для работы с iiko API.

#### Методы

- `authenticate(force: bool = False) -> str` - Выполнить авторизацию
- `logout() -> None` - Выполнить выход и освободить лицензию
- `request(method, endpoint, **kwargs) -> Response` - Выполнить HTTP запрос
- `get(endpoint, **kwargs) -> Response` - Выполнить GET запрос
- `post(endpoint, data=None, **kwargs) -> Response` - Выполнить POST запрос
- `put(endpoint, data=None, **kwargs) -> Response` - Выполнить PUT запрос
- `delete(endpoint, **kwargs) -> Response` - Выполнить DELETE запрос

#### Свойства

- `token: Optional[str]` - Текущий токен авторизации
- `is_authenticated: bool` - Проверка авторизации

### AuthManager

Управление авторизацией и токенами.

#### Методы

- `authenticate(force: bool = False) -> str` - Получить токен
- `logout() -> None` - Освободить лицензию
- `validate_token() -> bool` - Проверить валидность токена
- `refresh_if_needed() -> str` - Обновить токен если невалиден

### HTTPClient

Базовый HTTP клиент с автоматическими повторными попытками.

#### Методы

- `request(method, url, **kwargs) -> Response` - Выполнить запрос
- `get(url, **kwargs) -> Response` - GET запрос
- `post(url, data=None, **kwargs) -> Response` - POST запрос
- `put(url, data=None, **kwargs) -> Response` - PUT запрос
- `delete(url, **kwargs) -> Response` - DELETE запрос

## Важные замечания

### Авторизация и лицензии

⚠️ **ВАЖНО**: При авторизации занимается один слот лицензии!

- Токен рекомендуется переиспользовать, пока он не перестанет работать
- Если у вас только одна лицензия, повторная авторизация вызовет ошибку
- Всегда вызывайте `logout()` для освобождения лицензии
- Используйте context manager для автоматического освобождения лицензии

### Ограничения API

Согласно [рекомендациям iiko](https://ru.iiko.help/articles/#!api-documentations/printsipy-raboty):

1. **Последовательные запросы**: Запросы должны выполняться последовательно друг за другом
2. **Период данных**: Запрашивайте данные за период не длиннее одного месяца
3. **OLAP отчеты**: Используйте `build-summary=false` для крупных сетей
4. **Количество полей**: Не более 7 полей в OLAP-отчетах

SDK автоматически обеспечивает последовательное выполнение запросов.

### Типы запросов

#### POST запросы (form-urlencoded)

```python
# Создание/изменение сущности через параметры
sdk.post("/entity", data={"field1": "value1", "field2": "value2"})
```

#### PUT запросы (XML)

```python
# Создание/изменение сущности через XML
xml_data = """<?xml version="1.0" encoding="utf-8"?>
<entity>
    <field1>value1</field1>
</entity>"""

sdk.put("/entity", data=xml_data)
```

## Примеры

Запустите примеры использования:

```bash
uv run main.py
```

## Логирование

SDK использует стандартный модуль `logging`. Настройте логирование в вашем приложении:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

Уровни логирования:
- `INFO` - основные операции (авторизация, запросы)
- `DEBUG` - детальная информация (токены, параметры запросов)
- `WARNING` - предупреждения
- `ERROR` - ошибки

## Разработка

### Добавление зависимостей

```bash
uv add package_name
```

### Структура модулей

- `src/auth/` - Авторизация и управление токенами
- `src/client/` - HTTP клиент и сетевые операции
- `src/config/` - Конфигурация и настройки
- `src/models/` - Модели данных для API сущностей
- `src/utils/` - Вспомогательные утилиты

## Лицензия

MIT

## Ссылки

- [Документация iiko API](https://ru.iiko.help/articles/api-documentations/iikoserver-api)
- [Принципы работы с API](https://ru.iiko.help/articles/#!api-documentations/printsipy-raboty)
