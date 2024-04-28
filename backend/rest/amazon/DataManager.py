import time
from datetime import datetime, timedelta
from random import random
import pymongo
from core.db import MongoDBDataManager
from .base import DATETIME_PATTERN, now
from .order import AmazonOrderAPI, Marketplaces
from core.log import logger
from .product import AmazonCatalogAPI


class AmazonOrderMongoDBManager(MongoDBDataManager):
    def __init__(self, db_host: str, db_port: int,
                 marketplace=Marketplaces.DE):
        super().__init__(db_host, db_port)
        self.api = AmazonOrderAPI(marketplace=marketplace)
        self.db_name = "amazon_data"
        self.db_collection = "orders"

    def need_update(self, order: dict) -> bool:
        """
        Check if the order needs to be updated.
        :param order: Fetched order from Amazon API
        :return:
        """
        # Check if the order already exists in MongoDB
        mdb_orders_collection = self.db_client[self.db_name][self.db_collection]  # Select the collection for orders
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
        mdb_orders_collection = self.db_client[self.db_name][self.db_collection]

        if order is None:  # Fetch the order from Amazon API if not provided
            order = self.api.get_order(order_id).payload
            time.sleep(0.5)  # Wait for 1 second to avoid throttling

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
            try:
                order_id = order['AmazonOrderId']
                if self.need_update(order):
                    logger.info(f"Fetched Amazon order [{order_id}] purchased at {order['PurchaseDate']}...")
                    self.save_order(order_id, order=order)
            except Exception as e:
                logger.error(f"Error fetching order [{order_id}]: {e}")
                time.sleep(1)  # Wait for 1 second to avoid throttling

    def find_orders(self, **kwargs) -> list:
        mdb_orders_collection: pymongo.collection.Collection = self.db_client[self.db_name][self.db_collection]
        results = mdb_orders_collection.find(**kwargs)
        return list(results)

    # Group orders by date, count the number of items sold each day.
    def get_daily_mfn_sales(self, days_ago=7):
        start_date = datetime.now() - timedelta(days=days_ago)
        # Pipeline to group orders by date, count the number of items sold each day.
        pipeline = [
            {
                '$unwind': '$items.OrderItems'  # Unwind the items array to get each item
            }, {
                '$project': {
                    '_id': 0,
                    'orderDate': {
                        '$dateFromString': {
                            'dateString': '$order.PurchaseDate'
                        }
                    },
                    'asin': '$items.OrderItems.ASIN',
                    'quantityOrdered': '$items.OrderItems.QuantityOrdered',
                    'quantityShipped': '$items.OrderItems.QuantityShipped',
                    'sellerSKU': '$items.OrderItems.SellerSKU',
                    'title': '$items.OrderItems.Title',
                    'fulfillmentChannel': '$order.FulfillmentChannel',
                    'orderStatus': '$order.OrderStatus'
                }
            }, {
                '$match': {  # Filter orders that are not MFN and not canceled, and within the specified time range.
                    'orderStatus': {'$ne': 'Canceled'},
                    'fulfillmentChannel': 'MFN',
                    "orderDate": {"$gte": start_date},
                }
            }, {
                '$group': {
                    '_id': {
                        'date': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$orderDate'
                            }
                        },
                        'asin': '$asin'
                    },
                    'totalQuantityOrdered': {
                        '$sum': '$quantityOrdered'
                    },
                    'totalQuantityShipped': {
                        '$sum': '$quantityShipped'
                    },
                    'sellerSKU': {
                        '$first': '$sellerSKU'
                    },
                    'title': {
                        '$first': '$title'
                    }
                }
            },
            {'$sort': {'sellerSKU': 1 }},
            {
                '$group': {
                    '_id': '$_id.date',
                    'purchaseDate': {'$first': '$_id.date'},
                    'dailyOrdersItemsCount': {'$sum': '$totalQuantityOrdered'},
                    'dailyShippedItemsCount': {'$sum': '$totalQuantityShipped'},
                    'dailyShipments': {
                        '$push': {
                            'asin': '$_id.asin',
                            'sellerSKU': '$sellerSKU',
                            'totalQuantityShipped': '$totalQuantityShipped',
                            'totalQuantityOrdered': '$totalQuantityOrdered',
                            'title': '$title'
                        }
                    }
                }
            }, {
                '$sort': {
                    '_id': -1
                }
            }
        ]
        mdb_orders_collection: pymongo.collection.Collection = self.db_client[self.db_name][self.db_collection]
        results = mdb_orders_collection.aggregate(pipeline)
        return list(results)


# 插入数据
"""
获取订单列表，遍历订单列表，获取订单详情，获取订单状态和订单更新日期。
检查数据库中是否存在该订单，如果存在，则更新，如果不存在，则插入。
检查订单的最新更新日期是否有变化，如果有变化，则更新，如果没有变化，则跳过。
更新包括order和items两个文档。

每小时轮询一次，获取最近7天的订单，不包括亚马逊物流订单。
"""


class AmazonCatalogManager(MongoDBDataManager):

    def __init__(self, db_host: str, db_port: int,
                 marketplace=Marketplaces.DE):
        super().__init__(db_host, db_port)
        self.api = AmazonCatalogAPI(marketplace=marketplace)
        self.db_name = "amazon_data"
        self.db_collection = "catalog"

    def save_catalog(self, asin):
        mdb_catalog_collection = self.db_client[self.db_name][self.db_collection]
        # 从数据库中查找目录项
        item = mdb_catalog_collection.find_one({"_id": asin})
        # 如果数据库中没有此目录项，则从API获取
        if item is None:
            logger.info(f"Detected new catalog item [{asin}]...")
            item = self.api.get_catalog_item(asin)
            time.sleep(1)
        # 有 10% 的概率从API获取，并更新数据库
        else:
            if random() < 0.05:
                logger.info(f"Random selected catalog item [{asin}] to fetch again...")
                item = self.api.get_catalog_item(asin)
                time.sleep(1)
            else:
                item = item['catalogItem']


        document = {
            "_id": asin,
            "fetchAt": now(),
            "catalogItem": item,
        }

        result = mdb_catalog_collection.update_one(
            {"_id": asin},
            {"$set": document},
            upsert=True
        )
        return result

    def save_all_catalogs(self):
        # TODO 从mongodb中获取asin列表
        pipelines = [
            {
                '$unwind': '$items.OrderItems'
            }, {
                '$group': {
                    '_id': None,
                    'asinList': {
                        '$addToSet': '$items.OrderItems.ASIN'
                    }
                }
            }
        ]
        # Get all ASINs from orders collection
        mdb_catalog_collection = self.db_client[self.db_name]["orders"]
        results = mdb_catalog_collection.aggregate(pipelines)
        asinList = results.next()['asinList']

        # TODO 从api获取catalog, 并且保存到mongodb中
        for asin in asinList:
            self.save_catalog(asin)

    def get_catalog_item(self, asin):
        mdb_catalog_collection = self.db_client[self.db_name][self.db_collection]
        item = mdb_catalog_collection.find_one({"_id": asin})
        if item is None:
            logger.info(f"Catalog item [{asin}] not found in MongoDB...")
            return None
        else:
            return item['catalogItem']

    def get_all_catalog_items(self):
        mdb_catalog_collection = self.db_client[self.db_name][self.db_collection]
        items = mdb_catalog_collection.find()
        return list(items)

