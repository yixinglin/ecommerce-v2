import math
import time
from datetime import timedelta, datetime
import pymongo
from core.log import logger
from external.kaufland.base import Orders, Storefront, today, now, DATETIME_PATTERN, Client
from core.db import MongoDBDataManager


# TODO: 还没做重构，先放着不用管
class KauflandOrderSerice(MongoDBDataManager):

    def __init__(self, key_index, storefront: Storefront):
        super().__init__()
        client = Client.from_json(index=key_index)
        self.api = Orders(client=client, storefront=storefront)
        self.storefront = storefront
        self.db_name = "kaufland_data"
        self.db_collection = "orders"

    def need_update(self, order_brief: dict) -> bool:
        self.mdb_orders_collection = self.db_client[self.db_name][self.db_collection]
        # Order from API
        brief = order_brief
        order_id = brief['id_order']
        # Order from DB
        order_from_db = self.mdb_orders_collection.find_one({"_id": order_id})

        if order_from_db:
            # Check if order has been updated since the last fetch
            last_updated_at = datetime.strptime(brief["ts_units_updated_iso"],
                                                DATETIME_PATTERN)
            if last_updated_at > datetime.strptime(order_from_db['brief']["ts_units_updated_iso"], DATETIME_PATTERN):
                # Order has been updated, need to fetch it again
                return True
            else:
                return False
        else:  # Order does not exist in MongoDB, need to fetch it
            return True

    def save_order(self, order_brief: dict):
        mdb_orders_collection = self.db_client[self.db_name][self.db_collection]
        order_id = order_brief["id_order"]
        order = self.api.get_order(order_id)  # get order details from API
        time.sleep(0.5)

        document = {
            "_id": order_id,
            "brief": order_brief,
            "order": order['data'],
            "fetchedAt": now()
        }

        result = mdb_orders_collection.update_one(
            {"_id": order_id},
            {"$set": document},
            upsert=True
        )
        return result

    def save_all_orders(self, days_ago=7, **kwargs):
        start_date = (today() - timedelta(days=days_ago)).isoformat()
        orders_iterator = self.api.orders_iterator(createdAfter=start_date, **kwargs)
        total = math.inf
        orders = []  # list to store all orders
        for resp in orders_iterator:
            total = resp['pagination']["total"]
            orders += resp['data']
            time.sleep(0.5)
        assert total == len(orders), f"Total Kaufland orders {total} does not match number of orders {len(orders)}"

        if len(orders) > 0:
            for order_brief in orders:
                try:
                    if self.need_update(order_brief):
                        logger.info(
                            f"Fetching Kaufland order {order_brief['id_order']} created at {order_brief['ts_created_iso']}")
                        self.save_order(order_brief)
                except Exception as e:
                    logger.error(f"Error fetching order {order_brief['id_order']}: {e}")
                    time.sleep(1)  # wait 1 second before retrying
        return orders

    def get_daily_sales(self, days_ago=7):
        start_date = datetime.now() - timedelta(days=days_ago)
        pipeline = [
            {
                '$unwind': '$order.order_units'
            }, {
                '$match': {
                    "brief.ts_created_iso": {"$gte": start_date.isoformat()},
                    'order.order_units.status': {
                        '$ne': 'open'
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'orderDate': {
                        '$dateFromString': {
                            'dateString': '$brief.ts_created_iso'
                        }
                    },
                    'id_product': '$order.order_units.product.id_product',
                    'ean': {
                        '$first': '$order.order_units.product.eans'
                    },
                    'title': '$order.order_units.product.title',
                    'url': '$order.order_units.product.url',
                    'picture': '$order.order_units.product.main_picture',
                    'status': {
                        '$switch': {
                            'branches': [
                                {
                                    'case': {
                                        '$eq': [
                                            '$order.order_units.status', 'received'
                                        ]
                                    },
                                    'then': 'shipped'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$order.order_units.status', 'sent'
                                        ]
                                    },
                                    'then': 'shipped'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$order.order_units.status', 'sent_and_autopaid'
                                        ]
                                    },
                                    'then': 'shipped'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$order.order_units.status', 'need_to_be_sent'
                                        ]
                                    },
                                    'then': 'unshipped'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$order.order_units.status', 'returned'
                                        ]
                                    },
                                    'then': 'returned'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$order.order_units.status', 'returned_paid'
                                        ]
                                    },
                                    'then': 'returned'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$order.order_units.status', 'cancelled'
                                        ]
                                    },
                                    'then': 'cancelled'
                                }
                            ],
                            'default': 'Other'
                        }
                    }
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
                        'id_product': '$id_product',
                        'status': '$status'
                    },
                    'count': {
                        '$sum': 1
                    },
                    'ean': {
                        '$first': '$ean'
                    },
                    'title': {
                        '$first': '$title'
                    },
                    'url': {
                        '$first': '$url'
                    },
                    'picture': {
                        '$first': '$picture'
                    }
                }
            }, {
                '$group': {
                    '_id': {
                        'date': '$_id.date',
                        'status': '$_id.status'
                    },
                    'products': {
                        '$push': {
                            'productId': '$_id.id_product',
                            'ean': '$ean',
                            'count': '$count',
                            'picture': '$picture',
                            'url': '$url',
                            'title': '$title',
                            'count': '$count'
                        }
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'date': '$_id.date',
                    'status': '$_id.status',
                    'products': 1
                }
            }, {
                '$sort': {
                    'date': -1,
                    'status': -1
                }
            }
        ]
        mdb_orders_collection: pymongo.collection.Collection = self.db_client[self.db_name][self.db_collection]
        results = mdb_orders_collection.aggregate(pipeline)
        results = list(results)
        # Sort products by productId in descending order
        for result in results:
            sorted_products = sorted(result['products'], key=lambda x: x['productId'], reverse=True)
            result['products'] = sorted_products
        return results
