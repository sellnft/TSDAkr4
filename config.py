from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DB_USER: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    DB_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env")

    def get_db_url(self):
        return(f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

settings = Settings()
print("DB URL =>", settings.get_db_url())
print("DB HOST =>", settings.DB_HOST)