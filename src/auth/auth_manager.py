"""
Модуль управления авторизацией в iiko API.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from ..client import HTTPClient
from ..config import Settings

logger = logging.getLogger(__name__)


class TokenStorage:
    """
    Класс для хранения и управления токеном авторизации.

    Токен сохраняется в файл для переиспользования между запусками.
    """

    def __init__(self, storage_path: Path):
        """
        Инициализация хранилища токенов.

        Args:
            storage_path: Путь к файлу для хранения токена
        """
        self.storage_path = storage_path

    def save(self, token: str) -> None:
        """
        Сохранить токен в файл.

        Args:
            token: Токен авторизации
        """
        data = {
            "token": token,
            "created_at": datetime.now().isoformat(),
        }

        try:
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Токен сохранен в {self.storage_path}")
        except OSError as e:
            logger.warning(f"Не удалось сохранить токен: {e}")

    def load(self) -> str | None:
        """
        Загрузить токен из файла.

        Returns:
            Optional[str]: Токен если найден, иначе None
        """
        if not self.storage_path.exists():
            logger.debug("Файл с токеном не найден")
            return None

        try:
            with open(self.storage_path) as f:
                data = json.load(f)

            token = data.get("token")
            created_at = data.get("created_at")

            if token:
                logger.debug(f"Токен загружен из {self.storage_path}")
                if created_at:
                    logger.debug(f"Токен создан: {created_at}")
                return token

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Ошибка при загрузке токена: {e}")

        return None

    def clear(self) -> None:
        """Удалить сохраненный токен."""
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
                logger.debug(f"Токен удален из {self.storage_path}")
            except OSError as e:
                logger.warning(f"Не удалось удалить токен: {e}")


class AuthManager:
    """
    Менеджер авторизации для iiko API.

    Особенности:
    - Автоматическое получение и сохранение токена
    - Переиспользование токена между запусками
    - Корректное освобождение лицензии при выходе

    ВАЖНО:
    При авторизации занимается один слот лицензии.
    Рекомендуется использовать токен повторно, пока он не перестанет работать.
    """

    def __init__(self, settings: Settings, http_client: HTTPClient):
        """
        Инициализация менеджера авторизации.

        Args:
            settings: Экземпляр настроек приложения
            http_client: HTTP клиент для выполнения запросов
        """
        self.settings = settings
        self.http_client = http_client
        self.storage = TokenStorage(settings.token_storage_path)
        self._token: str | None = None

        # Попытка загрузить существующий токен
        self._load_saved_token()

    def _load_saved_token(self) -> None:
        """Загрузить сохраненный токен из хранилища."""
        saved_token = self.storage.load()
        if saved_token:
            self._token = saved_token
            logger.info("Загружен сохраненный токен")

    @property
    def token(self) -> str | None:
        """
        Получить текущий токен.

        Returns:
            Optional[str]: Текущий токен или None
        """
        return self._token

    @property
    def is_authenticated(self) -> bool:
        """
        Проверить, авторизован ли пользователь.

        Returns:
            bool: True если есть токен, иначе False
        """
        return self._token is not None

    def authenticate(self, force: bool = False) -> str:
        """
        Выполнить авторизацию и получить токен.

        ВАЖНО: При авторизации занимается один слот лицензии!
        Если у вас только одна лицензия, а токен уже получен,
        повторная авторизация вызовет ошибку.

        Args:
            force: Принудительная авторизация (получить новый токен)

        Returns:
            str: Токен авторизации

        Raises:
            requests.RequestException: Ошибка при авторизации
        """
        if self._token and not force:
            logger.info("Использую существующий токен")
            return self._token

        logger.info("Выполняю авторизацию в iiko API...")

        try:
            response = self.http_client.post(
                url=self.settings.auth_url,
                params={
                    "login": self.settings.rms_login,
                    "pass": self.settings.rms_password,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            token = response.text.strip()

            if not token:
                raise ValueError("Получен пустой токен от сервера")

            self._token = token
            self.storage.save(token)

            logger.info("✓ Авторизация успешна")
            logger.debug(f"Токен: {token[:20]}...")

            return token

        except requests.RequestException as e:
            logger.error(f"Ошибка авторизации: {e}")
            raise

    def logout(self) -> None:
        """
        Выполнить выход и освободить лицензию.

        Рекомендуется вызывать этот метод в конце работы,
        чтобы освободить слот лицензии для других пользователей.
        """
        if not self._token:
            logger.info("Токен отсутствует, выход не требуется")
            return

        logger.info("Выполняю выход из iiko API...")

        try:
            self.http_client.get(
                url=self.settings.logout_url, params={"key": self._token}
            )
            logger.info("✓ Выход выполнен успешно")

        except requests.RequestException as e:
            logger.warning(f"Ошибка при выходе: {e}")

        finally:
            # Очищаем токен в любом случае
            self._token = None
            self.storage.clear()

    def get_token(self) -> str:
        """
        Получить токен авторизации.

        Если токен уже есть, вернет его.
        Если токена нет, выполнит авторизацию.

        Returns:
            str: Токен авторизации

        Raises:
            requests.RequestException: Ошибка при авторизации
        """
        if not self._token:
            return self.authenticate()
        return self._token

    def validate_token(self) -> bool:
        """
        Проверить валидность текущего токена.

        Выполняет простой запрос к API для проверки работоспособности токена.

        Returns:
            bool: True если токен валиден, иначе False
        """
        if not self._token:
            return False

        try:
            # Попробуем выполнить простой запрос
            # Например, получить список организаций
            response = self.http_client.get(
                url=f"{self.settings.rms_base_url}/corporation/organizations",
                params={"key": self._token},
            )
            return response.status_code == 200

        except requests.RequestException:
            logger.debug("Токен невалиден")
            return False

    def refresh_if_needed(self) -> str:
        """
        Обновить токен если он невалиден.

        Returns:
            str: Валидный токен

        Raises:
            requests.RequestException: Ошибка при обновлении токена
        """
        if not self.validate_token():
            logger.info("Токен невалиден, выполняю повторную авторизацию...")
            self._token = None
            self.storage.clear()
            return self.authenticate()

        return self._token

    def __enter__(self):
        """Context manager entry."""
        self.get_token()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()
