import pymongo
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
import motor.motor_asyncio

from core.config import settings
from core.log import logger
from pymongo.errors import ServerSelectionTimeoutError


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