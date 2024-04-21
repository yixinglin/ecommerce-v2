import time
from datetime import datetime, timedelta

import pymongo
from pymongo.errors import ServerSelectionTimeoutError
from .order import AmazonOrderAPI, Marketplaces, DATETIME_PATTERN, now
from core.log import logger

class AmazonOrderMongoDBManager:
    def __init__(self, db_host: str, db_port: int,
                 marketplace=Marketplaces.DE):
        self.api = AmazonOrderAPI(marketplace=marketplace)
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = "amazon_data"
        self.db_collection = "orders"
        self.db_client = None

    def need_update(self, order: dict) -> bool:
        # order: Fetched order from Amazon API
        # Check if the order already exists in MongoDB
        mdb_orders_collection = self.db_client[self.db_name]["orders"]  # Select the collection for orders
        order_id = order["AmazonOrderId"]
        order_from_db = mdb_orders_collection.find_one({"_id": order_id})
        if order_from_db:  # Order already exists in MongoDB
            # Check if the order has been updated since the last fetch
            last_updated_at = datetime.strptime(order["LastUpdateDate"],
                                                DATETIME_PATTERN)  # The latest "LastUpdateDate"
            if last_updated_at > datetime.strptime(order_from_db['order']["LastUpdateDate"], DATETIME_PATTERN):
                # Order has been updated, need to fetch it again
                return True
            else:
                return False
        else:  # Order does not exist in MongoDB, need to fetch it
            return True

    def save_order(self, order_id: str, order: dict = None):
        """
        Save the order to MongoDB. If the order already exists in MongoDB, update it.
        If the order does not exist in MongoDB, insert it.
        """
        mdb_orders_collection = self.db_client[self.db_name]["orders"]
        # Check if the order already exists in MongoDB
        order_from_db = mdb_orders_collection.find_one({"_id": order_id})

        if order is None:  # Fetch the order from Amazon API if not provided
            order = self.api.get_order(order_id).payload
            time.sleep(0.5)  # Wait for 1 second to avoid throttling

        if order_from_db:  # Order already exists in MongoDB
            # Get the items of the order from MongoDB, because it's never be updated
            order_items = order_from_db["items"]
        else:
            order_items = self.api.get_order_items(order_id).payload
            time.sleep(0.5)  # Wait for 1 second to avoid throttling

        document = {
            "_id": order_id,
            "order": order,
            "items": order_items,
            "fetchedAt": now()
        }

        # Update the order if it already exists, otherwise insert it
        result = (mdb_orders_collection.update_one(
            {"_id": order_id},
            {"$set": document},
            upsert=True)
        )
        return result

    def save_all_orders(self, days_ago=30, **kwargs):
        orders = self.api.get_all_orders(days_ago=days_ago, **kwargs)
        for order in orders:
            order_id = order['AmazonOrderId']
            if self.need_update(order):
                logger.info(f"Fetched order [{order_id}] updated at {order['LastUpdateDate']}...")
                self.save_order(order_id, order=order)

    def find_orders(self, **kwargs) -> list:
        mdb_orders_collection: pymongo.collection.Collection = self.db_client[self.db_name]["orders"]
        results = mdb_orders_collection.find(**kwargs)
        return list(results)

    # Group orders by date, count the number of items sold each day.
    def get_daily_mfn_sales(self, days_ago=7):
        start_date = datetime.now() - timedelta(days=days_ago)
        # 聚合管道，用于统计每个产品每天的寄出数量
        pipeline = [
            {
                "$unwind": "$items.OrderItems"
            },
            {
                "$project": {
                    "_id": 0,
                    "orderDate": {"$dateFromString": {"dateString": "$order.PurchaseDate"}},
                    "asin": "$items.OrderItems.ASIN",
                    "quantityOrdered": "$items.OrderItems.QuantityOrdered",
                    "quantityShipped": "$items.OrderItems.QuantityShipped",
                    "sellerSKU": "$items.OrderItems.SellerSKU",
                    "fulfillmentChannel": "$order.FulfillmentChannel",
                    "title": "$items.OrderItems.Title"
                }
            },
            {
                "$match": {
                    "orderDate": {"$gte": start_date},
                    "fulfillmentChannel": "MFN"
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$orderDate"}},
                        "asin": "$asin"
                    },
                    "totalQuantityOrdered": {"$sum": "$quantityOrdered"},
                    "totalQuantityShipped": {"$sum": "$quantityShipped"},
                    "sellerSKU": {"$first": "$sellerSKU"},
                    "title": {"$first": "$title"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "purchaseDate": {"$first": "$_id.date"},
                    "dailyShipments": {
                        "$push": {
                            "asin": "$_id.asin",
                            "sellerSKU": "$sellerSKU",
                            "totalQuantityShipped": "$totalQuantityShipped",
                            "totalQuantityOrdered": "$totalQuantityOrdered",
                            "title": "$title",
                        }
                    }
                }
            },

            {
                "$sort": {"_id": -1}
            }
        ]
        mdb_orders_collection: pymongo.collection.Collection = self.db_client[self.db_name]["orders"]
        results = mdb_orders_collection.aggregate(pipeline)
        return list(results)

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


# 插入数据
"""
获取订单列表，遍历订单列表，获取订单详情，获取订单状态和订单更新日期。
检查数据库中是否存在该订单，如果存在，则更新，如果不存在，则插入。
检查订单的最新更新日期是否有变化，如果有变化，则更新，如果没有变化，则跳过。
更新包括order和items两个文档。

每小时轮询一次，获取最近7天的订单，不包括亚马逊物流订单。
"""
