# Doc: https://sellerapi.kaufland.com/?page=endpoints#/Orders/GetOrders
import hashlib
import hmac
import json
import math
import os
import time
from datetime import datetime
from enum import Enum
import requests
from core.config2 import settings
from core.log import logger

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'


class Storefront(Enum):
    DE = 'de'
    US = 'us'
    UK = 'uk'
    NL = 'nl'


def now():
    return datetime.now().strftime(DATETIME_PATTERN)


def today():
    return datetime.now().date()


class Client:

    def __init__(self, client_key, secret_key, account_id, **kwargs):
        self.client_key: str = client_key
        self.secret_key: str = secret_key
        self.account_id: str = account_id

    def sign_request(self, method, url, body, timestamp, secret_key):
        plain_text = "\n".join([method, url, body, str(timestamp)])
        digest_maker = hmac.new(secret_key.encode(),
                                None, hashlib.sha256)
        digest_maker.update(plain_text.encode())
        return digest_maker.hexdigest()

    def create_request_headers(self, method, url, body, client_key, secret_key):
        timestamp = str(int(time.time()))
        signature = self.sign_request(method, url, body, timestamp, secret_key)
        headers = {
            "Accept": 'application/json', 'Shop-Client-Key': client_key,
            "Shop-Timestamp": timestamp, "Shop-Signature": signature,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        }
        return headers

    @classmethod
    def from_json(cls, index):
        file_path = os.path.join('conf', 'apikeys',
                                 settings.api_keys.kaufland_api_keys)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = cls(**data['auth'][index])
        return k


class Orders:

    def __init__(self, client: Client, storefront: Storefront, **kwargs):
        """
         Init Kaufland orders API client
        :param client:  Kaufland client
        :param storefront: e.g. Storefront.DE
        :param kwargs:
        """
        self.client = client
        self.base_url = 'https://sellerapi.kaufland.com/v2'
        self.base_order_url = f'{self.base_url}/orders'
        self.storefront = storefront
        self.client_key = self.client.client_key
        self.secret_key = self.client.secret_key

    def get_order(self, order_id) -> dict:
        """
        Get order from Kaufland API by order_id
        :param order_id:  Kaufland order id
        :return:
        """
        url = f'{self.base_order_url}/{order_id}'
        # url = f'{self.base_order_url}/{order_id}?embedded=order_invoices'
        headers = self.client.create_request_headers("GET", url, "",
                                                     self.client_key, self.secret_key)
        logger.info(f"[API] Fetching Kaufland order [{order_id}]")
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise RuntimeError(f"Failed to get Kaufland order [{order_id}], status code: {res.status_code}")
        return json.loads(res.text)

    def get_orders(self, limit=100, offset=0, createdAfter=None) -> dict:
        """
        Get orders from Kaufland API
        :param limit: limit of orders to return
        :param offset: offset of orders to return
        :param createdAfter: get orders created after this date (ISO format)
        :return:
        """
        url = f'{self.base_order_url}?storefront={self.storefront.value}&limit={limit}&offset={offset}'
        if createdAfter is not None:
            url += f'&ts_created_from_iso={createdAfter}'
        headers = self.client.create_request_headers("GET", url, "", self.client_key, self.secret_key)
        logger.info(f"[API] Fetching Kaufland orders, limit: {limit}, offset: {offset}, createdAfter: {createdAfter}")
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise RuntimeError(f"Failed to get Kaufland orders, status code: {res.status_code}")
        return json.loads(res.text)

    def orders_iterator(self, **kwargs) -> iter:
        """
        Return an iterator of orders
        :param kwargs:
        :return: iterator of orders
        """
        limit = 100
        offset = 0
        total = math.inf
        while True:
            if offset > total - 1:
                break
            orders = self.get_orders(limit=limit, offset=offset, **kwargs)
            total = orders['pagination']["total"]
            offset += limit
            yield orders

    def get_order_units(self, limit, offset, status='recieved'):
        """
        返回每个订单的单元，会有重复的单号，需要统计合并
        'cancelled','need_to_be_sent','open','received','returned','returned_paid','sent','sent_and_autopaid'
        """
        if status is None:
            url = f"{self.base_url}/order-units?storefront={self.storefront.value}&sort=ts_created%3Adesc&limit={limit}&offset={offset}"
        else:
            url = f"{self.base_url}/order-units?storefront={self.storefront.value}&sort=ts_created%3Adesc&status={status}&limit={limit}&offset={offset}"
        headers = self.client.create_request_headers("GET", url, "", self.client_key, self.secret_key)
        logger.info(f"[API] Fetching Kaufland order units, limit: {limit}, offset: {offset}, status: {status}")
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise RuntimeError(f"Failed to get Kaufland order units, status code: {res.status_code}")
        return json.loads(res.text)

    def confirm_shipment(self):
        pass
