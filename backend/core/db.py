from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
import motor.motor_asyncio

from core.config import settings


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