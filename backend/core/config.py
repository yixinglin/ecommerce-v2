import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_ENV: str = os.getenv('API_ENV', 'dev')
    API_PREFIX: str
    API_VERSION: str
    PROJECT_NAME: str
    DEBUG: bool = os.getenv('DEBUG', 'True').strip().lower() in ['true', '1', 'yes', 'y']
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'info')

    API_PORT: int = os.getenv('API_PORT', 5000)
    API_HOST: str = os.getenv('API_HOST', '127.0.0.1')

    # Emails
    SMTP_SERVER: str
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    FROM_MAIL_NAME: str
    SMTP_SSL_TLS: bool = os.getenv('SMTP_SSL_TLS', 'False').strip().lower() in ['true', '1', 'yes', 'y']
    SMTP_PORT: int = os.getenv('SMTP_PORT', 587)

    # Sqlite Database
    DB_SQLITE_URI: str

    DB_MONGO_URI: str
    DB_MONGO_PORT: int = os.getenv('DB_MONGO_PORT', 27017)

    AMAZON_ACCESS_KEY:str
    METRO_ACCESS_KEY:str
    KAUFLAND_ACCESS_KEY:str


    def __init__(self, _env_file=None, **values):
        super().__init__(**values)


settings = Settings(_env_file=None)
pass