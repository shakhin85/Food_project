"""
Главный SDK клиент для работы с iiko API.
"""

import logging
from typing import Optional, Dict, Any

import requests

from .config import Settings, get_settings
from .client import HTTPClient
from .auth import AuthManager
from .reports import OLAPReports

logger = logging.getLogger(__name__)


class IikoSDK:
    """
    Python SDK для работы с iiko API.

    Предоставляет высокоуровневый интерфейс для работы с API iiko.
    Автоматически управляет авторизацией и токенами.

    Пример использования:
        >>> from src import IikoSDK
        >>>
        >>> # Создание клиента
        >>> sdk = IikoSDK()
        >>>
        >>> # Авторизация (выполняется автоматически)
        >>> sdk.authenticate()
        >>>
        >>> # Выполнение запросов
        >>> response = sdk.request("GET", "/nomenclature")
        >>> print(response.text)
        >>>
        >>> # Или с помощью context manager (автоматический logout)
        >>> with IikoSDK() as sdk:
        ...     response = sdk.request("GET", "/nomenclature")
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Инициализация SDK клиента.

        Args:
            settings: Экземпляр настроек. Если None, будет создан автоматически.
        """
        self.settings = settings or get_settings()
        self.http_client = HTTPClient(self.settings)
        self.auth = AuthManager(self.settings, self.http_client)
        self._olap: Optional[OLAPReports] = None

        logger.info("iiko SDK инициализирован")

    @property
    def is_authenticated(self) -> bool:
        """
        Проверить, авторизован ли клиент.

        Returns:
            bool: True если есть токен
        """
        return self.auth.is_authenticated

    @property
    def token(self) -> Optional[str]:
        """
        Получить текущий токен авторизации.

        Returns:
            Optional[str]: Токен или None
        """
        return self.auth.token

    @property
    def olap(self) -> OLAPReports:
        """
        Получить интерфейс для работы с OLAP-отчетами.

        Returns:
            OLAPReports: Интерфейс OLAP-отчетов
        """
        if self._olap is None:
            self._olap = OLAPReports(self)
        return self._olap

    def authenticate(self, force: bool = False) -> str:
        """
        Выполнить авторизацию.

        Args:
            force: Принудительная авторизация (получить новый токен)

        Returns:
            str: Токен авторизации

        Raises:
            requests.RequestException: Ошибка при авторизации
        """
        return self.auth.authenticate(force=force)

    def logout(self) -> None:
        """
        Выполнить выход и освободить лицензию.

        Рекомендуется вызывать в конце работы.
        """
        self.auth.logout()

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        authenticated: bool = True,
        **kwargs
    ) -> requests.Response:
        """
        Выполнить запрос к iiko API.

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: Конечная точка API (например, "/nomenclature")
            params: Query параметры
            data: Данные для отправки
            authenticated: Требуется ли авторизация (по умолчанию True)
            **kwargs: Дополнительные параметры

        Returns:
            requests.Response: Ответ от сервера

        Raises:
            requests.RequestException: Ошибка при выполнении запроса
        """
        # Формируем полный URL
        url = f"{self.settings.rms_base_url}/{endpoint.lstrip('/')}"

        # Добавляем токен если требуется авторизация
        if authenticated:
            token = self.auth.get_token()
            if params is None:
                params = {}
            params["key"] = token

        # Выполняем запрос
        return self.http_client.request(
            method=method,
            url=url,
            params=params,
            data=data,
            **kwargs
        )

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Выполнить GET запрос.

        Args:
            endpoint: Конечная точка API
            **kwargs: Дополнительные параметры

        Returns:
            requests.Response: Ответ от сервера
        """
        return self.request("GET", endpoint, **kwargs)

    def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        **kwargs
    ) -> requests.Response:
        """
        Выполнить POST запрос.

        Args:
            endpoint: Конечная точка API
            data: Данные для отправки
            **kwargs: Дополнительные параметры

        Returns:
            requests.Response: Ответ от сервера
        """
        return self.request("POST", endpoint, data=data, **kwargs)

    def put(
        self,
        endpoint: str,
        data: Optional[str] = None,
        **kwargs
    ) -> requests.Response:
        """
        Выполнить PUT запрос.

        Args:
            endpoint: Конечная точка API
            data: XML данные
            **kwargs: Дополнительные параметры

        Returns:
            requests.Response: Ответ от сервера
        """
        return self.request("PUT", endpoint, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Выполнить DELETE запрос.

        Args:
            endpoint: Конечная точка API
            **kwargs: Дополнительные параметры

        Returns:
            requests.Response: Ответ от сервера
        """
        return self.request("DELETE", endpoint, **kwargs)

    def close(self) -> None:
        """Закрыть все соединения."""
        self.http_client.close()

    def __enter__(self):
        """Context manager entry."""
        self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        auth_status = "authenticated" if self.is_authenticated else "not authenticated"
        return f"<IikoSDK({auth_status})>"
