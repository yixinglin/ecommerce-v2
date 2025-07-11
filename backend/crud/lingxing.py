from typing import List

from pymongo import UpdateOne

from core.log import logger
from core.db import AsyncMongoDBDataManager



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

class AsyncLingxingListingDB(AsyncMongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "lingxing_data"
        self.db_collection_name = "listings"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    async def save_listing(self, listing_id, document):
        collection = self.get_db_collection()
        try:
            result = await collection.update_one(
                {"_id": listing_id},
                {"$set": document},
                upsert=True
            )
            return result
        except Exception as e:
            logger.error(f"Failed to save listing {listing_id}: {e}")
            raise

    async def query_listings_by_listing_ids(self, listing_ids: List[str]):
        collection = self.get_db_collection()
        cursor = collection.find({"_id": {"$in": listing_ids}, "data.is_delete": 0})
        result = [doc async for doc in cursor]
        return result

    async def query_listings_by_fnsku(self, fnsku: str):
        collection = self.get_db_collection()
        cursor = collection.find({"data.fnsku": fnsku, "data.is_delete": 0})
        result = [doc async for doc in cursor]
        return result

    async def query_listings_by_seller_sku(self, sku: str):
        collection = self.get_db_collection()
        cursor = collection.find({"data.seller_sku": sku, "data.is_delete": 0})
        result = [doc async for doc in cursor]
        return result

    async def query_all_listings(self, offset=0, limit=100, filter_=None, *args, **kwargs):
        collection = self.get_db_collection()
        if filter_:
            filter_.update({"data.is_delete": 0})
        else:
            filter_ = {"data.is_delete": 0}
        cursor = collection.find(filter=filter_, *args, **kwargs).skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def query_listings_by_sid(self, sid: int):
        collection = self.get_db_collection()
        cursor = collection.find({"data.sid": sid, "data.is_delete": 0})
        result = [doc async for doc in cursor]
        return result


class AsyncLingxingBasicDataDB(AsyncMongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "lingxing_data"
        self.db_collection_name_sellers = "sellers"
        self.db_collection_name_marketplaces = "marketplaces"

    async def save_seller(self, seller_id, document):
        collection = self.db_client[self.db_name][self.db_collection_name_sellers]
        try:
            result = await collection.update_one(
                {"_id": seller_id},
                {"$set": document},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Inserted new seller with ID: {result.upserted_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to save seller {seller_id}: {e}")
            raise

    async def query_seller(self, seller_id):
        collection = self.db_client[self.db_name][self.db_collection_name_sellers]
        result = await collection.find_one({"_id": seller_id})
        return result

    async def query_all_sellers(self):
        collection = self.db_client[self.db_name][self.db_collection_name_sellers]
        cursor = collection.find()
        result = [doc async for doc in cursor]
        return result

    async def save_marketplace(self, marketplace_id, document):
        collection = self.db_client[self.db_name][self.db_collection_name_marketplaces]
        try:
            result = await collection.update_one(
                {"_id": marketplace_id},
                {"$set": document},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Inserted new marketplace with ID: {result.upserted_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to save marketplace {marketplace_id}: {e}")
            raise

    async def query_all_marketplaces(self):
        collection = self.db_client[self.db_name][self.db_collection_name_marketplaces]
        cursor = collection.find()
        result = [doc async for doc in cursor]
        return result


class AsyncLingxingInventoryDB(AsyncMongoDBDataManager):
    def __init__(self):
        super().__init__()
        self.db_name = "lingxing_data"
        self.db_collection_inventory = "inventory"
        self.db_collection_inventory_bin = "inventory_bin"
        self.db_collection_fba_inventory = "fba_inventory"

    async def save_inventory(self, inventory_id, document):
        collection = self.db_client[self.db_name][self.db_collection_inventory]
        try:
            result = await collection.update_one(
                {"_id": inventory_id},
                {"$set": document},
                upsert=True
            )
            return result
        except Exception as e:
            logger.error(f"Failed to save inventory {inventory_id}: {e}")
            raise

    async def query_all_inventory(self, offset=0, limit=100):
        collection = self.db_client[self.db_name][self.db_collection_inventory]
        cursor = collection.find().skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def query_inventory(self, offset=0, limit=100, *args, **kwargs):
        collection = self.db_client[self.db_name][self.db_collection_inventory]
        cursor = collection.find(*args, **kwargs).skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def delete_all_inventory(self):
        collection = self.db_client[self.db_name][self.db_collection_inventory]
        result = await collection.delete_many({})
        return result

    async def save_inventory_bin(self, inventory_bin_id, document):
        collection = self.db_client[self.db_name][self.db_collection_inventory_bin]
        try:
            result = await collection.update_one(
                {"_id": inventory_bin_id},
                {"$set": document},
                upsert=True
            )
            return result
        except Exception as e:
            logger.error(f"Failed to save inventory bin {inventory_bin_id}: {e}")
            raise

    async def query_all_inventory_bin(self, offset=0, limit=100):
        collection = self.db_client[self.db_name][self.db_collection_inventory_bin]
        cursor = collection.find().skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def query_inventory_bin(self, offset=0, limit=100, *args, **kwargs):
        collection = self.db_client[self.db_name][self.db_collection_inventory_bin]
        cursor = collection.find(*args, **kwargs).skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def delete_all_inventory_bin(self):
        collection = self.db_client[self.db_name][self.db_collection_inventory_bin]
        result = await collection.delete_many({})
        return result

    async def save_fba_inventory(self, fba_inventory_id, document):
        collection = self.db_client[self.db_name][self.db_collection_fba_inventory]
        try:
            result = await collection.insert_one(document)
            return result
        except Exception as e:
            logger.error(f"Failed to save fba_inventory {fba_inventory_id}: {e}")
            raise

    async def query_all_fba_inventory(self, offset=0, limit=100):
        collection = self.db_client[self.db_name][self.db_collection_fba_inventory]
        cursor = collection.find().skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def query_fba_inventory(self, offset=0, limit=100, *args, **kwargs):
        collection = self.db_client[self.db_name][self.db_collection_fba_inventory]
        cursor = collection.find(*args, **kwargs).skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def delete_all_fba_inventory(self):
        collection = self.db_client[self.db_name][self.db_collection_fba_inventory]
        result = await collection.delete_many({})
        return result


class AsyncLingxingFbaShipmentPlanDB(AsyncMongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "lingxing_data"
        self.db_collection_fba_shipment_plan = "fba_shipment_plan"

    async def save_fba_shipment_plan(self, fba_shipment_plan_id, document):
        collection = self.db_client[self.db_name][self.db_collection_fba_shipment_plan]
        try:
            result = await collection.update_one(
                {"_id": fba_shipment_plan_id},
                {"$set": document},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Inserted new fba_shipment_plan with ID: {result.upserted_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to save fba_shipment_plan {fba_shipment_plan_id}: {e}")
            raise

    async def query_fba_shipment_plan_by_ispg_id(self, ispg_id: int):
        collection = self.db_client[self.db_name][self.db_collection_fba_shipment_plan]
        result = await collection.find_one({"_id": ispg_id})
        return result

    async def query_fba_shipment_plan_by_seq(self, seq_code: str):
        collection = self.db_client[self.db_name][self.db_collection_fba_shipment_plan]
        result = await collection.find_one({"data.seq": seq_code})
        return result

    async def query_all_fba_shipment_plans(self, offset=0, limit=100, *args, **kwargs):
        # Add query conditions
        collection = self.db_client[self.db_name][self.db_collection_fba_shipment_plan]
        cursor = collection.find(*args, **kwargs).skip(offset).limit(limit)
        result = [doc async for doc in cursor]
        return result


class AsyncLingxingOrderDB(AsyncMongoDBDataManager):
    def __init__(self):
        super().__init__()
        self.db_name = "lingxing_data"
        self.db_collection_orders = "orders"
        self.db_collection_order_details = "order_details"

    async def save_order(self, order_id, document):
        collection = self.db_client[self.db_name][self.db_collection_orders]
        try:
            result = await collection.update_one(
                {"_id": order_id},
                {"$set": document},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Inserted new order with ID: {result.upserted_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to save order {order_id}: {e}")
            raise

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

    async def query_orders(self, offset=0, limit=None, *args, **kwargs):
        collection = self.db_client[self.db_name][self.db_collection_orders]
        cursor = (collection.find(*args, **kwargs)
                  .sort("data.purchase_date_local", -1)
                  .skip(offset))
        if limit:
            cursor = cursor.limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def query_all_orders(self, offset=0, limit=None):
        collection = self.db_client[self.db_name][self.db_collection_orders]
        cursor = (collection.find()
                  .sort("data.purchase_date_local", -1)
                  .skip(offset))
        if limit:
            cursor = cursor.limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def save_order_detail(self, order_detail_id, document):
        collection = self.db_client[self.db_name][self.db_collection_order_details]
        try:
            result = await collection.update_one(
                {"_id": order_detail_id},
                {"$set": document},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Inserted new order_detail with ID: {result.upserted_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to save order_detail {order_detail_id}: {e}")
            raise

    async def bulk_save_order_details(self, documents):
        collection = self.db_client[self.db_name][self.db_collection_order_details]
        return await bulk_upsert(
            collection,
            documents,
            ordered=False
        )

    async def query_order_detail(self, order_id):
        collection = self.db_client[self.db_name][self.db_collection_order_details]
        result = await collection.find_one({"_id": order_id})
        return result

    async def query_order_details(self, offset=0, limit=None, *args, **kwargs):
        collection = self.db_client[self.db_name][self.db_collection_order_details]
        cursor = (collection.find(*args, **kwargs)
                  .sort("data.purchase_date_local", -1)
                  .skip(offset))
        if limit:
            cursor = cursor.limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def query_all_order_details(self, offset=0, limit=None):
        collection = self.db_client[self.db_name][self.db_collection_order_details]
        cursor = (collection.find()
                  .sort("data.purchase_date_local", -1)
                  .skip(offset))
        if limit:
            cursor = cursor.limit(limit)
        result = [doc async for doc in cursor]
        return result

    async def query_all_ids(self, collection_name):
        collection = self.db_client[self.db_name][collection_name]
        cursor = collection.find({}, {"_id": 1})  # 查询全部，只返回 _id 字段
        return [doc["_id"] async for doc in cursor]


