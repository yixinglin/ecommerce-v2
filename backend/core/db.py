import datetime
import glob
import os
import subprocess
import time
from abc import abstractmethod
from typing import List, Optional
import pymongo
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
from core.config2 import settings
from core.log import logger
from pymongo.errors import ServerSelectionTimeoutError
from models.orders import StandardOrder
import redis
import json

from models.shipment import StandardShipment

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'
BACKUP_DIR = settings.static.backup_dir
os.makedirs(BACKUP_DIR, exist_ok=True)

def init_db_sqlite(app: FastAPI):
    register_tortoise(
        app,
        db_url=settings.DB_SQLITE_URI,
        modules={"models": ["models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )


def init_db_mysql_for_app(app: FastAPI):
    db_url = f"mysql://{settings.mysql.user}:{settings.mysql.password}@{settings.mysql.host}:{settings.mysql.port}/{settings.mysql.database}"
    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": ["models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )

async def init_db_mysql_async():
    await Tortoise.init(
        db_url=f"mysql://{settings.mysql.user}:{settings.mysql.password}@{settings.mysql.host}:{settings.mysql.port}/{settings.mysql.database}",
        modules={"models": ["models"]},
    )


def backup_mysql_db():
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{BACKUP_DIR}/backup_{settings.mysql.database}_{now}.sql"
    command = [
        "mysqldump",
        "-h", settings.mysql.host,
        "-P", str(settings.mysql.port),
        "-u", settings.mysql.user,
        f"-p'{settings.mysql.password}'",
        settings.mysql.database
    ]

    try:
        with open(filename, "w") as f:
            subprocess.run(command, stdout=f, check=True)
        logger.info(f"[{now}] Backup successful: {filename}")
    except subprocess.CalledProcessError as e:
        logger.error(f"[{now}] Backup failed: {e}")
        return

def clean_old_mysql_db_backups(retain_days=7):
    cutoff = time.time() - (retain_days * 86400)
    for file in glob.glob(f"{BACKUP_DIR}/backup_*.sql"):
        if os.path.getmtime(file) < cutoff:
            os.remove(file)
            logger.info(f"Removed old backup file：{file}")

redis_pool = None

class RedisDataManager:
    def __init__(self, *args, **kwargs):
        self.redis_host = settings.redis.host
        self.redis_port = settings.redis.port
        # self.redis_client = settings.REDIS_USERNAME
        # self.redis_password = settings.REDIS_PASSWORD
        self.redis_db = settings.redis.db
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

    def scan(self, pattern: str) -> List[str]:
        cursor = '0'
        keys = []
        while cursor != 0:
            cursor, partial_keys = self.client.scan(cursor, match=pattern)
            keys.extend(partial_keys)
        data = {key: self.client.get(key) for key in keys}
        return data

    def get_ttl(self, key: str) -> int:
        return self.client.ttl(key)

    def set_json(self, key: str, value: dict, time_to_live_sec: int = None):
        self.client.set(key, json.dumps(value))
        if time_to_live_sec:
            self.client.expire(key, time_to_live_sec)

    def get_json(self, key: str) -> dict:
        # return json.loads(self.client.get(key))
        value = self.client.get(key)
        ttl = self.client.ttl(key)
        if value:
            data = json.loads(value)
            data['ttl'] = ttl
            return data
        else:
            return None


class MongoDBDataManager:

    def __init__(self):
        self.db_host = settings.mongodb.host
        self.db_port = settings.mongodb.port
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

    def delete_random_documents(
        self,
        database_name: str,
        collection_name: str,
        percentage: float = 0.1,
        min_delete: int = 1,
        max_delete: int = 100,
        dry_run: bool = False,
        **kwargs,
    ) -> Optional[int]:
        """
        随机删除 MongoDB 某集合中指定百分比的文档。
        :param database_name: 数据库名
        :param collection_name: 集合名
        :param percentage: 要删除的比例 (默认 0.1 表示 10%)
        :param min_delete: 至少删除的最小条数（防止 0 条）
        :param dry_run: 如果为 True，仅返回将删除的文档数，不实际删除
        :return: 实际删除的文档数量，或 None（dry_run 时）
        """
        client = self.db_client
        collection = client[database_name][collection_name]
        logger.info(f"正在删除文档{database_name}-{collection_name}")

        total_docs = collection.count_documents({})
        delete_count = max(int(total_docs * percentage), min_delete)
        delete_count = min(delete_count, max_delete)

        if delete_count == 0:
            logger.info("文档过少，无需删除。")
            return 0

        # 随机抽样文档
        pipeline = [{"$sample": {"size": delete_count}}]
        random_docs = list(collection.aggregate(pipeline))
        ids_to_delete = [doc["_id"] for doc in random_docs]

        if dry_run:
            logger.info(f"[Dry Run] 将删除 {len(ids_to_delete)} 条文档。")
            return None

        result = collection.delete_many({"_id": {"$in": ids_to_delete}})
        logger.info(f"已删除 {result.deleted_count} 条文档。")
        return result.deleted_count

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


import motor.motor_asyncio

class AsyncMongoDBDataManager:
    def __init__(self):
        self.db_host = settings.mongodb.host
        self.db_port = settings.mongodb.port
        self.db_client = None

    def get_client(self):
        return self.db_client

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self.db_client:
            self.db_client.close()
            self.db_client = None

    async def connect(self):
        try:
            host = f"mongodb://{self.db_host}:{self.db_port}"
            self.db_client = motor.motor_asyncio.AsyncIOMotorClient(host)  # Connect
            # names = self.db_client.list_database_names()
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise RuntimeError("Error connecting to MongoDB") from e
        return self

