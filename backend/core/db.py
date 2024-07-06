from typing import List
import pymongo
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
import motor.motor_asyncio
from core.config import settings
from core.log import logger
from pymongo.errors import ServerSelectionTimeoutError
from models.orders import StandardOrder

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'

def init_db_sqlite(app: FastAPI):
    register_tortoise(
        app,
        db_url=settings.DB_SQLITE_URI,
        modules={"models": ["models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )



def init_mongodb():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.DB_MONGO_URI)
    database = client[settings.DB_MONGO_DATABASE]
    collection = database.get_collection(settings.DB_MONGO_COLLECTION)


class MongoDBDataManager:

    def __init__(self, db_host: str, db_port: int):
        self.db_host = db_host
        self.db_port = db_port
        self.db_client = None

    def __enter__(self):
        # Connect to MongoDB
        try:
            self.db_client = pymongo.MongoClient(self.db_host, self.db_port, serverSelectionTimeoutMS=10000)  # Connect
            names = self.db_client.list_database_names()
        except ServerSelectionTimeoutError as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise RuntimeError("Error connecting to MongoDB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db_client:
            self.db_client.close()
        del self

class OrderQueryParams:
    limit: int = 100
    offset: int = 0
    purchasedDateFrom: str = None  # Should be in YYYY-MM-ddTHH:mm:ssZ format
    purchasedDateTo: str = None   # Should be in YYYY-MM-ddTHH:mm:ssZ format
    status: List[str] = None
    orderIds: List[str] = None

class OrderMongoDBDataManager(MongoDBDataManager):
    def __init__(self, db_host: str, db_port: int):
        super().__init__(db_host, db_port)
    def find_orders(self, filter_:dict, *args, **kwargs) -> List[StandardOrder]:
        raise NotImplementedError()

    def find_order_by_id(self, id:str, *args, **kwargs) -> StandardOrder:
        raise NotImplementedError()

    def find_orders_by_ids(self, ids:str, *args, **kwargs) -> List[StandardOrder]:
        raise NotImplementedError()

    def find_unshipped_orders(self, *args, **kwargs) -> List[StandardOrder]:
        raise NotImplementedError()

class ShipmentMongoDBDataManager(MongoDBDataManager):

    def __init__(self, db_host: str, db_port: int):
        super().__init__(db_host, db_port)

    def find_shipments(self, filter_:dict) -> List[StandardOrder]:
        raise NotImplementedError()

    def find_shipment_by_id(self, id:str) -> StandardOrder:
        raise NotImplementedError()

    def find_shipments_by_ids(self, ids:str) -> List[StandardOrder]:
        raise NotImplementedError()