import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_ENV: str = os.getenv('API_ENV', 'dev')
    API_PREFIX: str = os.getenv('API_PREFIX')
    API_VERSION: str = os.getenv('API_VERSION')
    PROJECT_NAME: str = os.getenv('PROJECT_NAME')
    DEBUG: bool = os.getenv('DEBUG', True)
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'info')

    API_PORT: int = os.getenv('API_PORT', 5000)
    API_HOST: str = os.getenv('API_HOST', '127.0.0.1')

    # Emails
    SMTP_SERVER: str = os.getenv('SMTP_SERVER')
    SMTP_USERNAME: str = os.getenv('SMTP_USER')
    SMTP_PASSWORD: str = os.getenv('SMTP_USERNAME')
    FROM_EMAIL: str = os.getenv('FROM_EMAIL')
    FROM_MAIL_NAME: str = os.getenv('FROM_MAIL_NAME')
    SMTP_SSL_TLS: bool = os.getenv('SMTP_SSL_TLS', False)
    SMTP_PORT: int = os.getenv('SMTP_PORT', 587)

    # Sqlite Database
    DB_SQLITE_URI: str = os.getenv('DB_SQLITE_URI')

    DB_MONGO_URI: str = os.getenv('DB_MONGO_URI')
    DB_MONGO_DATABASE: str = os.getenv('DB_MONGO_DATABASE')


settings = Settings()
