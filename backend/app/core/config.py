"""Config central via .env — nunca hardcodar segredos no código."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    DATABASE_URL: str = ""
    JWT_SECRET: str = "dev-only-trocar"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    ENV: str = "dev"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    HE_EMAIL_DESTINO: str = ""
    AI_PROVIDER: str = "local"
    AI_API_KEY: str = ""


settings = Settings()
