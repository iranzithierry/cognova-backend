from pydantic import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    FRONTEND_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
