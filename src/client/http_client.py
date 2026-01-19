"""
Базовый HTTP клиент для работы с iiko API.
"""

import time
import logging
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import Settings

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Базовый HTTP клиент для выполнения запросов к iiko API.

    Особенности:
    - Автоматические повторные попытки при ошибках
    - Логирование всех запросов
    - Поддержка различных типов контента (form-data, XML)
    - Соблюдение рекомендаций iiko API (последовательные запросы)
    """

    def __init__(self, settings: Settings):
        """
        Инициализация HTTP клиента.

        Args:
            settings: Экземпляр настроек приложения
        """
        self.settings = settings
        self.session = self._create_session()
        self._last_request_time: Optional[float] = None

    def _create_session(self) -> requests.Session:
        """
        Создать сессию с настройками повторных попыток.

        Returns:
            requests.Session: Настроенная сессия
        """
        session = requests.Session()

        # Настройка повторных попыток
        retry_strategy = Retry(
            total=self.settings.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _ensure_sequential_requests(self) -> None:
        """
        Гарантировать последовательное выполнение запросов.

        Согласно рекомендациям iiko API, запросы должны выполняться
        последовательно друг за другом.
        """
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            # Минимальная задержка между запросами 100ms
            min_delay = 0.1
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Выполнить HTTP запрос.

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            url: URL для запроса
            params: Query параметры
            data: Данные для отправки (dict для form-data, str для XML)
            headers: Заголовки запроса
            **kwargs: Дополнительные параметры для requests

        Returns:
            requests.Response: Ответ от сервера

        Raises:
            requests.RequestException: Ошибка при выполнении запроса
        """
        # Гарантируем последовательность запросов
        self._ensure_sequential_requests()

        # Устанавливаем таймаут если не указан
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.settings.request_timeout

        # Подготовка заголовков
        if headers is None:
            headers = {}

        # Логирование запроса
        logger.info(f"{method} {url}")
        if params:
            logger.debug(f"Params: {params}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                **kwargs
            )

            # Логирование ответа
            logger.info(f"Response: {response.status_code}")
            logger.debug(f"Response body: {response.text[:200]}...")

            # Проверка статуса
            response.raise_for_status()

            return response

        finally:
            # Запоминаем время последнего запроса
            self._last_request_time = time.time()

    def get(self, url: str, **kwargs) -> requests.Response:
        """Выполнить GET запрос."""
        return self.request("GET", url, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Выполнить POST запрос.

        Args:
            url: URL для запроса
            data: Данные (dict для form-urlencoded, str для XML)
            **kwargs: Дополнительные параметры

        Returns:
            requests.Response: Ответ от сервера
        """
        headers = kwargs.pop("headers", {})

        # Если data - строка, считаем что это XML
        if isinstance(data, str):
            headers["Content-Type"] = "application/xml"
        elif isinstance(data, dict):
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        return self.request("POST", url, data=data, headers=headers, **kwargs)

    def put(
        self,
        url: str,
        data: Optional[str] = None,
        **kwargs
    ) -> requests.Response:
        """
        Выполнить PUT запрос (обычно с XML данными).

        Args:
            url: URL для запроса
            data: XML данные
            **kwargs: Дополнительные параметры

        Returns:
            requests.Response: Ответ от сервера
        """
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/xml"

        return self.request("PUT", url, data=data, headers=headers, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """Выполнить DELETE запрос."""
        return self.request("DELETE", url, **kwargs)

    def close(self) -> None:
        """Закрыть сессию."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
