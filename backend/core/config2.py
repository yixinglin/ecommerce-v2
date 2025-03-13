import os
import sys
import tomllib
from pydantic import BaseModel
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# sudo apt-get install fonts-wqy-zenhei
if sys.platform == 'linux':
    pdfmetrics.registerFont(TTFont('noto', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'))
    FONT = 'noto'
elif sys.platform == 'win32':
    pdfmetrics.registerFont(TTFont('simsun', 'C:/Windows/Fonts/SimSun.ttc'))
    FONT ='simsun'


class AppConfig(BaseModel):
    project_name: str
    debug: bool
    log_level: str
    env: str
    version: str
    port: int
    host: str
    domain: str
    prefix: str

class SmtpConfig(BaseModel):
    server: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str
    ssl_tls: bool
    starttls: bool

class MongoDBConfig(BaseModel):
    host: str
    port: int

class MySqlConfig(BaseModel):
    user: str
    password: str
    host: str
    port: int
    database: str

class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    username: str
    password: str

class SSLConfig(BaseModel):
    cert_file: str
    key_file: str
    enabled: bool

class ApiKeysConfig(BaseModel):
    amazon_access_key: str
    metro_access_key: str
    kaufland_access_key: str
    odoo_access_key: str
    odoo_access_key_index: int
    gls_access_key: str
    gls_access_key_index: int
    lingxing_access_key: str
    lingxing_access_key_index: int

class HttpProxyConfig(BaseModel):
    config_file: str
    index: int
    enabled: bool

class SchedulerConfig(BaseModel):
    interval_seconds: int
    amazon_orders_fetch_enabled: bool
    amazon_products_fetch_enabled: bool
    kaufland_orders_fetch_enabled: bool
    gls_tracking_fetch_enabled: bool
    lingxing_fetch_enabled: bool

class Config(BaseModel):
    app: AppConfig
    mongodb: MongoDBConfig
    mysql: MySqlConfig
    redis: RedisConfig
    ssl: SSLConfig
    api_keys: ApiKeysConfig
    http_proxy: HttpProxyConfig
    scheduler: SchedulerConfig


# 获取 `env` 环境变量（默认为 `dev`）
env = os.getenv("ENV", "dev")

# 计算配置文件路径
config_file = f"conf/{env}.toml"

# 读取 TOML 文件
try:
    with open(config_file, "rb") as f:
        config_dict = tomllib.load(f)  # Python 3.11+
except FileNotFoundError:
    raise FileNotFoundError(f"配置文件 '{config_file}' 未找到！")

# 解析为 Pydantic 配置对象
settings = Config.parse_obj(config_dict)


if __name__ == '__main__':
    with open('../conf/dev.toml', 'rb') as f:
        config_dict = tomllib.load(f)
        config = Config.parse_obj(config_dict)
        print(config)