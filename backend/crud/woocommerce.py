from pymongo import UpdateOne

from core.db import AsyncMongoDBDataManager
from core.log import logger


async def bulk_upsert(
    collection,
    documents,
    ordered=False
):
    operations = []
    id_field = "_id"
    for doc in documents:
        if id_field not in doc:
            raise ValueError(f"Documents must have field '{id_field}': {doc}")
        operations.append(
            UpdateOne(
                {id_field: doc[id_field]},
                {"$set": doc},
                upsert=True
            )
        )

    if not operations:
        logger.info("No documents to upsert")
        return 0

    try:
        result = await collection.bulk_write(operations, ordered=ordered)
        return result.upserted_count
    except Exception as e:
        logger.error(f"Failed to upsert documents: {e}")
        raise


class AsyncWoocommerceOrderDB(AsyncMongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "woocommerce_data"
        self.db_collection_orders = "orders"

    async def bulk_save_orders(self, documents):
        collection = self.db_client[self.db_name][self.db_collection_orders]
        return await bulk_upsert(
            collection,
            documents,
            ordered=False
        )

    async def query_order(self, order_id):
        collection = self.db_client[self.db_name][self.db_collection_orders]
        result = await collection.find_one({"_id": order_id})
        return result

    async def query_orders(self, offset=0, limit=10, filter: dict = None):
        collection = self.db_client[self.db_name][self.db_collection_orders]
        query = filter or {}
        total = await collection.count_documents(query)
        cursor = collection.find(query).sort("date_created", -1)
        cursor = cursor.skip(offset).limit(limit)
        data = [doc async for doc in cursor]
        return {
            "data": data,
            "total": total,
        }
