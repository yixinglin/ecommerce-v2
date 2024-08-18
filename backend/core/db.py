from abc import abstractmethod
from typing import List
import pymongo
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
from core.config import settings
from core.log import logger
from pymongo.errors import ServerSelectionTimeoutError
from models.orders import StandardOrder
import redis
import json

from models.shipment import StandardShipment

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'


def init_db_sqlite(app: FastAPI):
    register_tortoise(
        app,
        db_url=settings.DB_SQLITE_URI,
        modules={"models": ["models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )

redis_pool = None

class RedisDataManager:
    def __init__(self, *args, **kwargs):
        self.redis_host = settings.REDIS_HOST
        self.redis_port = settings.REDIS_PORT
        # self.redis_client = settings.REDIS_USERNAME
        # self.redis_password = settings.REDIS_PASSWORD
        self.redis_db = settings.REDIS_DB
        self.encoding = 'utf-8'

        if not redis_pool:
            redis.ConnectionPool(max_connections=100)
        self.client = redis.Redis(host=self.redis_host,
                                  port=self.redis_port,
                                  db=self.redis_db,
                                  decode_responses=True,
                                  connection_pool=redis_pool, **kwargs)

    def set(self, key: str, value: str, time_to_live_sec: int = None):
        self.client.set(key, value)
        if time_to_live_sec:
            self.client.expire(key, time_to_live_sec)

    def get(self, key: str) -> str:
        return self.client.get(key)

    def delete(self, key: str):
        self.client.delete(key)

    def set_json(self, key: str, value: dict, time_to_live_sec: int = None):
        self.client.set(key, json.dumps(value))
        if time_to_live_sec:
            self.client.expire(key, time_to_live_sec)

    def get_json(self, key: str) -> dict:
        return json.loads(self.client.get(key))


class MongoDBDataManager:

    def __init__(self):
        self.db_host = settings.DB_MONGO_URI
        self.db_port = settings.DB_MONGO_PORT
        self.db_client = None

    def connect(self):
        # Connect to MongoDB
        try:
            self.db_client = pymongo.MongoClient(self.db_host, self.db_port, serverSelectionTimeoutMS=10000)  # Connect
            names = self.db_client.list_database_names()
        except ServerSelectionTimeoutError as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise RuntimeError("Error connecting to MongoDB")
        return self

    def get_client(self):
        return self.db_client

    def set_client(self, client):
        self.db_client = client
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        del self

    def close(self):
        if self.db_client:
            self.db_client.close()

class OrderQueryParams:
    limit: int = 100
    offset: int = 0
    purchasedDateFrom: str = None  # Should be in YYYY-MM-ddTHH:mm:ssZ format
    purchasedDateTo: str = None  # Should be in YYYY-MM-ddTHH:mm:ssZ format
    status: List[str] = None
    orderIds: List[str] = None


class OrderMongoDBDataManager(MongoDBDataManager):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def query_orders(self, filter_: dict, *args, **kwargs) -> List[StandardOrder]:
        raise NotImplementedError()

    @abstractmethod
    def query_order_by_id(self, id: str, *args, **kwargs) -> StandardOrder:
        raise NotImplementedError()

    @abstractmethod
    def query_orders_by_ids(self, ids: str, *args, **kwargs) -> List[StandardOrder]:
        raise NotImplementedError()

    @abstractmethod
    def query_unshipped_orders(self, *args, **kwargs) -> List[StandardOrder]:
        raise NotImplementedError()

    @abstractmethod
    def save_order(self, order_id, document):
        raise NotImplementedError()

    @abstractmethod
    def update_order(self, order_id, document) -> StandardOrder:
        raise NotImplementedError()

    @abstractmethod
    def delete_order(self, id: str, *args, **kwargs) -> bool:
        raise NotImplementedError()


class ShipmentMongoDBDataManager(MongoDBDataManager):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def query_shipments(self, filter_: dict) -> List[StandardShipment]:
        raise NotImplementedError()

    @abstractmethod
    def query_shipment_by_id(self, id: str) -> StandardShipment:
        raise NotImplementedError()

    @abstractmethod
    def query_shipments_by_ids(self, ids: str) -> List[StandardShipment]:
        raise NotImplementedError()


    @abstractmethod
    def save_shipment(self, document):
        raise NotImplementedError()

    @abstractmethod
    def delete_shipment(self, id: str, *args, **kwargs) -> bool:
        raise NotImplementedError()


    def get_shipment_id(self, shipment: StandardShipment):
        return ";".join(shipment.references)