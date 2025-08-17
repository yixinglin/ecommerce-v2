import json
import os

import requests
from pydantic import BaseModel

from core.config2 import settings

"""
以下是对Woocommerce API的封装，使用JWT Token进行身份验证。
需要配合 JWT Authentication for WP-API 插件使用
"""
__version__ = "1.0.0"

# Date pattern in woocommerce api
DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%S'
DATE_PATTERN = '%Y-%m-%d'

class ApiKey(BaseModel):
    name: str
    url: str
    username: str
    password: str
    version: str

    @classmethod
    def from_json(cls, index, type_='woo-jwt'):
        file_path = os.path.join('conf', 'apikeys',
                                 settings.api_keys.wp_access_key)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = cls(
            name=data['keys'][index]['name'],
            **data['keys'][index][type_])
        print(f"Using API Key: {data['keys'][index]['name']}")
        return k

class API(object):
    """WooCommerce JWT REST API Client"""

    def __init__(self, url, username, password, token=None, **kwargs):
        self.site_url = url.rstrip("/")
        self.username = username
        self.password = password
        self.version = kwargs.get("version", "wc/v3")
        self.timeout = kwargs.get("timeout", 10)
        self.user_agent = kwargs.get("user_agent", f"WooCommerce-Python-REST-API/{__version__}")
        self.token = token or self._get_token()

    def _get_token(self):
        """获取 JWT Token"""
        print("Getting JWT Token...")
        token_url = f"{self.site_url}/wp-json/jwt-auth/v1/token"
        headers = {"Content-Type": "application/json", "User-Agent": self.user_agent}
        payload = {"username": self.username, "password": self.password}

        response = requests.post(token_url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json().get("token")
    
    def validate_token(self):
        """验证 JWT Token 是否有效"""
        validate_url = f"{self.site_url}/wp-json/jwt-auth/v1/token/validate"
        headers = self._headers()
        
        response = requests.post(validate_url, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Token validation failed: {response.text}")

    def _headers(self):
        """生成带认证的请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent
        }
    
    def get(self, endpoint, params=None):
        """GET 请求"""
        url = f"{self.site_url}/wp-json/{self.version}/{endpoint.lstrip('/')}"
        response = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
        # response.raise_for_status()
        return response

    def post(self, endpoint, data=None):
        """POST 请求"""
        url = f"{self.site_url}/wp-json/{self.version}/{endpoint.lstrip('/')}"
        response = requests.post(url, headers=self._headers(), json=data, timeout=self.timeout)
        # response.raise_for_status()
        return response
    
    def put(self, endpoint, data=None):
        """PUT 请求"""
        url = f"{self.site_url}/wp-json/{self.version}/{endpoint.lstrip('/')}"
        response = requests.put(url, headers=self._headers(), json=data, timeout=self.timeout)
        # response.raise_for_status()
        return response

    def delete(self, endpoint, params=None):
        """DELETE 请求"""
        url = f"{self.site_url}/wp-json/{self.version}/{endpoint.lstrip('/')}"
        response = requests.delete(url, headers=self._headers(), params=params, timeout=self.timeout)
        # response.raise_for_status()
        return response
    
class WPAPI_V2(API):
    """WordPress JWT REST API Client"""
    
    def __init__(self, url, username, password, **kwargs):
        super().__init__(url, username, password, **kwargs)
        self.version = kwargs.get("version", "wp/v2")
    
    def get(self, endpoint, params=None):        
        return super().get(endpoint, params)
    
    def post(self, endpoint, data=None):        
        return super().post(endpoint, data)
    
    def put(self, endpoint, data=None):        
        return super().put(endpoint, data)
    
    def delete(self, endpoint, params=None):        
        return super().delete(endpoint, params)
    
class WCAPI_V3(API):
    """WooCommerce REST API Client"""
    
    def __init__(self, url, username, password, **kwargs):
        super().__init__(url, username, password, **kwargs)
        self.version = kwargs.get("version", "wc/v3")
    
    def get(self, endpoint, params=None):        
        return super().get(endpoint, params)
    
    def post(self, endpoint, data=None):        
        return super().post(endpoint, data)
    
    def put(self, endpoint, data=None):        
        return super().put(endpoint, data)
    
    def delete(self, endpoint, params=None):        
        return super().delete(endpoint, params)

class WooClient(API):
    """WooCommerce REST API Client"""

    def __init__(self, key:ApiKey, **kwargs):
        super().__init__(
            url=key.url,
            username=key.username,
            password=key.password,
            version=key.version,
            **kwargs
        )
        self.key = key
