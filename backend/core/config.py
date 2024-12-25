import os
import sys

from pydantic_settings import BaseSettings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class Settings(BaseSettings):
    API_ENV: str = os.getenv('API_ENV', 'dev')
    API_PREFIX: str
    API_VERSION: str
    PROJECT_NAME: str
    DEBUG: bool = os.getenv('DEBUG', 'True').strip().lower() in ['true', '1', 'yes', 'y']
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'info')

    API_PORT: int = os.getenv('API_PORT', 5000)
    API_HOST: str = os.getenv('API_HOST', '127.0.0.1')
    API_DOMAIN: str = os.getenv('API_DOMAIN', 'http://localhost')

    # Emails
    SMTP_SETTINGS: str  # Path to SMTP settings file (JSON)

    # SSL
    SSL_ENABLED: bool = os.getenv('SSL_ENABLED', 'False').strip().lower() in ['true', '1', 'yes', 'y']
    SSL_CERT_FILE: str = os.getenv('SSL_CERT_FILE', None)
    SSL_KEY_FILE: str = os.getenv('SSL_KEY_FILE', None)

    # Sqlite Database
    DB_SQLITE_URI: str
    # MongoDB Database
    DB_MONGO_URI: str
    DB_MONGO_PORT: int = os.getenv('DB_MONGO_PORT', 27017)
    # Redis Cache
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = os.getenv('REDIS_PORT', 6379)
    REDIS_DB: int = os.getenv('REDIS_DB', 0)
    REDIS_USERNAME: str = os.getenv('REDIS_USERNAME', None)
    REDIS_PASSWORD: str = os.getenv('REDIS_PASSWORD', None)

    AMAZON_ACCESS_KEY: str
    METRO_ACCESS_KEY: str
    KAUFLAND_ACCESS_KEY: str
    ODOO_ACCESS_KEY: str
    ODOO_ACCESS_KEY_INDEX: int
    GLS_ACCESS_KEY: str
    GLS_ACCESS_KEY_INDEX: int
    LINGXING_ACCESS_KEY: str
    LINGXING_ACCESS_KEY_INDEX: int

    HTTP_PROXY: str
    HTTP_PROXY_ENABLED: bool
    HTTP_PROXY_INDEX: int

    SCHEDULER_INTERVAL_SECONDS: int = os.getenv('SCHEDULER_INTERVAL_SECONDS', 3600)
    SCHEDULER_AMAZON_ORDERS_FETCH_ENABLED: bool = os.getenv('SCHEDULER_AMAZON_ORDERS_FETCH_ENABLED', 'False').strip().lower() in ['true', '1', 'yes', 'y']
    SCHEDULER_KAUFLAND_ORDERS_FETCH_ENABLED: bool = os.getenv('SCHEDULER_KAUFLAND_ORDERS_FETCH_ENABLED', 'False').strip().lower() in ['true', '1', 'yes', 'y']

    SCHEDULER_AMAZON_PRODUCTS_FETCH_ENABLED: bool = os.getenv('SCHEDULER_AMAZON_PRODUCTS_FETCH_ENABLED', 'False').strip().lower() in ['true', '1', 'yes', 'y']
    SCHEDULER_GLS_TRACKING_FETCH_ENABLED: bool = os.getenv('SCHEDULER_GLS_TRACKING_FETCH_ENABLED', 'False').strip().lower() in ['true', '1', 'yes', 'y']
    SCHEDULER_LINGXING_FETCH_ENABLED: bool = os.getenv('SCHEDULER_LINGXING_FETCH_ENABLED', 'False').strip().lower() in ['true', '1', 'yes', 'y']

    def __init__(self, _env_file=None, **values):
        super().__init__(**values)


settings = Settings(_env_file=None)


# sudo apt-get install fonts-wqy-zenhei
if sys.platform == 'linux':
    pdfmetrics.registerFont(TTFont('noto', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'))
    FONT = 'noto'
elif sys.platform == 'win32':
    pdfmetrics.registerFont(TTFont('simsun', 'C:/Windows/Fonts/SimSun.ttc'))
    FONT ='simsun'



