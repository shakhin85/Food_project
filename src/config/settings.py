"""
Конфигурация для iiko API SDK.
Использует pydantic-settings для валидации и загрузки настроек из .env файла.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки для работы с iiko API."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # API настройки
    rms_base_url: str = Field(
        ...,
        description="Базовый URL для iiko API (например, https://server.iiko.it/resto/api)",
    )
    rms_login: str = Field(..., description="Логин для авторизации в iiko API")
    rms_password: str = Field(..., description="Пароль для авторизации в iiko API")

    # Настройки токена
    token_storage_path: Path = Field(
        default=Path(".token"),
        description="Путь к файлу для хранения токена авторизации",
    )

    # Настройки запросов
    request_timeout: int = Field(
        default=30, description="Таймаут для HTTP запросов в секундах", ge=1, le=300
    )

    max_retries: int = Field(
        default=3,
        description="Максимальное количество попыток повтора запроса",
        ge=0,
        le=10,
    )

    @field_validator("rms_base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Валидация и нормализация базового URL."""
        v = v.rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("rms_base_url должен начинаться с http:// или https://")
        return v

    @property
    def auth_url(self) -> str:
        """Полный URL для авторизации."""
        return f"{self.rms_base_url}/auth"

    @property
    def logout_url(self) -> str:
        """Полный URL для выхода."""
        return f"{self.rms_base_url}/logout"


# Глобальный экземпляр настроек (singleton)
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Получить экземпляр настроек (singleton pattern).

    Returns:
        Settings: Экземпляр настроек приложения
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Сбросить кэшированные настройки (для тестирования)."""
    global _settings
    _settings = None
