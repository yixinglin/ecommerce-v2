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
    SMTP_HOST: str = os.getenv('SMTP_HOST')
    SMTP_USER: str = os.getenv('SMTP_USER')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD')
    EMAILS_FROM_EMAIL: str = os.getenv('EMAILS_FROM_EMAIL')
    SMTP_TLS: bool = os.getenv('SMTP_TLS', True)
    SMTP_SSL: bool = os.getenv('SMTP_SSL', False)
    SMTP_PORT: int = os.getenv('SMTP_PORT', 587)



settings = Settings()