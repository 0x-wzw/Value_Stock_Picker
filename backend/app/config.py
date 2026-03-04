from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Value Stock Picker"
    debug: bool = False

    # Database — individual components (matches origin/main pattern)
    postgres_server: str = "localhost"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "value_stock_picker"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}/{self.postgres_db}"

    # Auth
    secret_key: str = "changeme-in-production-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # External APIs
    # SEC EDGAR requires a User-Agent header identifying the requester
    sec_user_agent: str = "ValueStockPicker admin@example.com"
    # Alpha Vantage (optional, free tier available at alphavantage.co)
    alpha_vantage_api_key: str = ""

    # Cache TTLs (seconds)
    price_cache_ttl: int = 60          # 1 min for real-time prices
    fundamentals_cache_ttl: int = 3600  # 1 hour for fundamentals
    filings_cache_ttl: int = 86400      # 24 hours for SEC filings

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
