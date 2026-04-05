from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class TelegramSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TELEGRAM_", extra="ignore")

    bot_token: str = Field(..., description="Telegram Bot API token")
    webhook_url: str = Field("", description="Webhook URL for production")
    webhook_secret: str = Field("", description="Webhook secret token")
    api_id: int = Field(0, description="Telegram MTProto API ID (для парсинга каналов)")
    api_hash: str = Field("", description="Telegram MTProto API Hash")
    channels: str = Field("", description="Comma-separated channel usernames (без @)")

    @property
    def channels_list(self) -> list[str]:
        if not self.channels:
            return []
        return [ch.strip() for ch in self.channels.split(",") if ch.strip()]


class OpenRouterSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENROUTER_", extra="ignore")

    api_key: str = Field("", description="OpenRouter API key")
    max_tokens: int = Field(4096, description="Max tokens per response")


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    host: str = Field("db")
    port: int = Field(5432)
    db: str = Field("stazka")
    user: str = Field("stazka_user")
    password: str = Field("stazka_password")

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    host: str = Field("redis")
    port: int = Field(6379)
    password: str = Field("")
    db: int = Field(0)

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field("development", alias="APP_ENV")
    debug: bool = Field(True, alias="DEBUG")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")
    api_secret_key: str = Field("change_me", alias="API_SECRET_KEY")

    @property
    def is_production(self) -> bool:
        return self.env == "production"


class SuperJobSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SUPERJOB_", extra="ignore")

    api_key: str = Field("", description="SuperJob API key")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    openrouter: OpenRouterSettings = Field(default_factory=OpenRouterSettings)
    superjob: SuperJobSettings = Field(default_factory=SuperJobSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    app: AppSettings = Field(default_factory=AppSettings)


settings = Settings()
