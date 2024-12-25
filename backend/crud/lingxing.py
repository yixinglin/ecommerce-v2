from typing import List

from core.log import logger
from core.db import AsyncMongoDBDataManager
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
            # if result.upserted_id:
            #     logger.info(f"Inserted new listing with ID: {result.upserted_id}")
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

