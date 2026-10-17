from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = 'development'
    
    postgres_user: str
    postgres_password: str
    postgres_db: str
    database_url: str

    redis_url: str

settings = Settings() 