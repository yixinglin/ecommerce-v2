import time
from datetime import datetime, timedelta
from random import random
from typing import List
from pymongo.collection import Collection
from sp_api.base import Marketplaces, SellingApiRequestThrottledException
from core.db import MongoDBDataManager, OrderMongoDBDataManager, OrderQueryParams
from core.log import logger
from models.orders import OrderItem, StandardOrder, OrderStatus
from models.shipment import Address
from utils.city import is_company_name, alpha2_to_country_name
from utils.stringutils import jsonpath, isEmpty, remove_duplicates
from .base import DATETIME_PATTERN, now, AmazonSpAPIKey, AmazonAddress
from .order import AmazonOrderAPI
from .product import AmazonCatalogAPI


# https://developer-docs.amazon.com/sp-api/docs/orders-api-v0-reference#updateshipmentstatus
# MAP_ORDER_STATUS = {
#     OrderStatus.pending: "Pending",
#     OrderStatus.confirmed: "Unshipped",
#     OrderStatus.processing: "Unshipped",
#     OrderStatus.shipped: "Shipped",
#     OrderStatus.cancelled: "Canceled",
# }

MAP_ORDER_STATUS = {
    "Pending": OrderStatus.pending.value,
    "Unshipped": OrderStatus.confirmed.value,
    "Shipped": OrderStatus.shipped.value,
    "Canceled": OrderStatus.cancelled.value,
}

class AmazonOrderMongoDBManager(OrderMongoDBDataManager):
    """
    This class is used to manage Amazon orders in MongoDB.
    """
    FILTER_01 = {"order.OrderStatus": "Unshipped",
              "order.FulfillmentChannel": "MFN"}

    def __init__(self,  key_index: int,
                 marketplace: Marketplaces, *args, **kwargs):
        """
         Initialize the AmazonOrderMongoDBManager.
        :param db_host: Host of the MongoDB server.
        :param db_port:   Port of the MongoDB server.
        :param key_index:  Index of the API key to use.
        :param marketplace:  e.g. Marketplaces.DE
        """
        super().__init__(*args, **kwargs)
        self.db_name = "amazon_data"
        self.db_collection = "orders"
        self.marketplace = marketplace
        if key_index is not None:
            api_key = AmazonSpAPIKey.from_json(key_index)
            logger.info(f"Using API key {api_key.account_id} for Amazon marketplace {marketplace.name}")
            self.api = AmazonOrderAPI(api_key=api_key, marketplace=marketplace)
            self.account_id = api_key.account_id
            self.salesChannel = self.api.salesChannel

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
        Fetch the order from Amazon API and save it to MongoDB. If the order already exists in MongoDB, update it.
        If the order does not exist in MongoDB, insert it.
        :param order_id: Amazon order ID
        :param order: Fetched order from Amazon API, if not provided, it will be fetched from Amazon API.
        """
        mdb_orders_collection = self.db_client[self.db_name][self.db_collection]

        if order is None:  # Fetch the order from Amazon API if not provided
            order = self.api.get_order(order_id).payload
            time.sleep(0.5)  # Wait for 1 second to avoid throttling

        order_items = self.api.get_order_items(order_id).payload
        time.sleep(0.7)  # Wait for 1 second to avoid throttling

        # Check if the order has been stored in MongoDB
        order_from_db = mdb_orders_collection.find_one({"_id": order_id})
        if order_from_db:  # Order already exists in MongoDB
            shipping_address = order_from_db['order'].get('ShippingAddress', None)
            order['ShippingAddress'] = shipping_address

        document = {
            "_id": order_id,
            "order": order,
            "items": order_items,
            "account_id": self.api.get_account_id(),
            "fetchedAt": now()
        }

        # Update the order if it already exists, otherwise insert it
        result = (mdb_orders_collection.update_one(
            {"_id": order_id},
            {"$set": document},
            upsert=True)
        )
        return result

    def __standard_to_amazon_address(self, address: Address) -> AmazonAddress:
        if is_company_name(address.name1):
            companyName = address.name1
            name = address.name2
            addressline2 = address.name3
        elif is_company_name(address.name2):
            companyName = address.name2
            name = address.name1
            addressline2 = address.name3
        else:
            companyName = address.name3
            name = address.name1
            addressline2 = address.name2

        return AmazonAddress(
            CompanyName=companyName,
            Name=name,
            AddressLine1=address.street1,
            AddressLine2=addressline2,
            City=address.city,
            Country=alpha2_to_country_name(address.country),
            CountryCode=address.country,
            StateOrRegion=address.province,
            PostalCode=address.zipCode,
            Phone=address.mobile,
        )

    def __amazon_to_standard_address(self, address: AmazonAddress) -> Address:
        if isEmpty(address.CompanyName):
            name1 = address.Name
            name2 = address.AddressLine2
            name3 = address.CompanyName
        elif isEmpty(address.Name):
            name1 = address.CompanyName
            name2 = address.AddressLine2
            name3 = address.Name
        else:
            name1 = address.CompanyName
            name2 = address.Name
            name3 = address.AddressLine2

        return Address(
            name1=name1,
            name2=name2,
            name3=name3,
            street1=address.AddressLine1,
            zipCode=address.PostalCode,
            city=address.City,
            province=address.StateOrRegion,
            country=address.CountryCode,
            email="",
            telephone="",
            mobile=""
        )


    def add_shipping_address_to_order(self, order_id: str, shipping_address: Address) -> bool:
        """
        Add shipping address to an order in MongoDB.
        :param order_id: Amazon order ID
        :param shipping_address: Shipping address to add to the order
        Doc: https://developer-docs.amazon.com/sp-api/docs/orders-api-v0-reference#address
       """
        amazonAddress = self.__standard_to_amazon_address(shipping_address)
        ship_addr = amazonAddress.dict()
        mdb_orders_collection = self.db_client[self.db_name][self.db_collection]
        # Check if the order has been stored in MongoDB
        order_from_db = mdb_orders_collection.find_one({"_id": order_id})
        if order_from_db:  # Order already exists in MongoDB
            # Update the order with the shipping address
            result = (mdb_orders_collection.update_one(
                {"_id": order_id},
                {"$set": {"order.ShippingAddress": ship_addr}},
                upsert=True)
            )
        else:
            # Fetch the order from Amazon API and add the shipping address
            order = self.api.get_order(order_id).payload
            order['ShippingAddress'] = ship_addr
            # Save the order to MongoDB
            result = self.save_order(order_id, order=order)
        return result

    def add_pack_slip_to_order(self, order_id: str, pack_slip: str):
        """
        Add pack slip to an order in MongoDB.
        :param order_id:
        :param pack_slip:
        :return:
        """
        mdb_orders_collection = self.db_client[self.db_name][self.db_collection]
        # Check if the order has been stored in MongoDB
        order_from_db = mdb_orders_collection.find_one({"_id": order_id})
        # if order dose not exist in MongoDB, fetch the order from Amazon API and add the pack slip
        if not order_from_db:
            order = self.api.get_order(order_id).payload
            self.save_order(order_id, order=order)

        # Update the order with the pack slip
        result = (mdb_orders_collection.update_one(
            {"_id": order_id},
            {"$set": {"packslip": pack_slip}},
            upsert=True)
        )

        return result

    def save_all_orders(self, days_ago=30, **kwargs):
        """
        Save all orders within the specified time range to MongoDB.
        :param days_ago: Number of days to fetch orders from
        :param kwargs: Additional filters for the orders, e.g. FulfillmentChannels=["MFN"]
        :return:
        Example:
        save_all_orders(days_ago=30, FulfillmentChannels=["MFN"])
        """
        orders = self.api.get_all_orders(days_ago=days_ago, **kwargs)
        for order in orders:
            try:
                order_id = order['AmazonOrderId']
                if self.need_update(order):
                    logger.info(f"Fetched Amazon order [{order_id}] purchased at {order['PurchaseDate']}...")
                    self.save_order(order_id, order=order)
            except SellingApiRequestThrottledException as e:
                logger.error(f"Throttled while fetching order [{order_id}]: {e}, Error Type: {type(e).__name__}")
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error fetching order [{order_id}]: {e}, Error Type: {type(e).__name__}")
                time.sleep(1)  # Wait for 1 second to avoid throttling

    def find_orders(self, offset=0, limit=9999, **kwargs) -> List[StandardOrder]:
        """
        Find orders in MongoDB.

        @Note: This function is a low-level function. Do not modify without proper review.

        :param kwargs: filter conditions
        :return:
        Example:
        find_orders(filter={"order.OrderStatus": "Unshipped", "order.FulfillmentChannel": "MFN"})
        """
        orders_collection:Collection = self.db_client[self.db_name][self.db_collection]
        results = list(orders_collection.find(**kwargs)
                       .sort({"order.PurchaseDate": -1})
                       .skip(offset)
                       .limit(limit)
                       )
        results = [self.to_standard_order(r) for r in results]
        return results

    def find_orders_by_query_params(self, query_params: OrderQueryParams) -> List[StandardOrder]:
        query = {}
        if query_params.purchasedDateTo:
            query.setdefault("order.PurchaseDate", {})["$lte"] = query_params.purchasedDateTo

        if query_params.purchasedDateFrom:
            query.setdefault("order.PurchaseDate", {})["$gte"] = query_params.purchasedDateFrom

        if query_params.status:
            query['order.OrderStatus'] = {"$in": query_params.status}

        if query_params.orderIds:
            query['_id'] = {"$in": query_params.orderIds}


        query['account_id'] = self.api.get_account_id()
        return self.find_orders(filter=query)



    def find_orders_by_ids(self, ids: List[str]) -> List[StandardOrder]:
        """
        Find orders by IDs in MongoDB while preserving the order of the given IDs.

        @Note: This function is a low-level function. Do not modify without proper review.

        :param ids:
        :return:
        """
        filter_ = {"_id": {"$in": ids}}
        orders = list(self.find_orders(filter=filter_))
        # Sort the orders by the given order IDs
        if len(orders) > 0:
            order_dict = {order.orderId: order for order in orders}
            orders = [order_dict[id] for id in ids]
        return orders

    def find_order_by_id(self, order_id: str) -> StandardOrder:
        """
        Find an order by ID in MongoDB.
        @Note: This function is a low-level function. Do not modify without proper review.

        :param order_id:
        :return:
        """
        result = self.find_orders_by_ids([order_id])
        if result:
            return result[0]
        else:
            return None

    def find_unshipped_orders(self, days_ago=7, up_to_date=True) -> List[StandardOrder]:
        """
        Get all FBM orders within the specified time range via Amazon API, and save them to MongoDB.
        The function will return a list of up-to-date FBM orders.
        :param days_ago: Number of days to fetch orders from
        :return: List of up-to-date FBM orders
        """
        # Fetch all FBM orders within the specified time range and save them to MongoDB
        if up_to_date:
            self.save_all_orders(days_ago=days_ago, FulfillmentChannels=["MFN"])
        # Get all FBM orders within the specified time range
        filter_ = {
            "order.FulfillmentChannel": "MFN",
            "order.OrderStatus": "Unshipped",
        }
        if hasattr(self, 'account_id'):
            filter_['account_id'] = self.account_id
        if hasattr(self,'salesChannel'):
            filter_['order.SalesChannel'] = self.salesChannel
        orders = self.find_orders(filter=filter_)
        return orders


    def to_standard_order(self, order: dict) -> StandardOrder:
        orderId = order['_id']
        orderItems = order['items']['OrderItems']
        standardOrderItems = []
        for item in orderItems:
            quantity = int(jsonpath(item, '$.QuantityOrdered', 0))
            unit_price = float(jsonpath(item, '$.ItemPrice.Amount', 0.0))
            tax = float(jsonpath(item, '$.ItemTax.Amount', 0.0))
            stdItem = OrderItem(id=item['ASIN'],
                                name=item['Title'],
                                sku=item['SellerSKU'],
                                asin=item['ASIN'],
                                ean="",
                                quantity=quantity,
                                unitPrice=unit_price,
                                subtotal=unit_price * quantity,
                                tax=tax,
                                total=unit_price * quantity + tax,
                                description="",
                                image="")
            additionalFields = {
                "isTransparency": bool(jsonpath(item, '$.IsTransparency', False)),
            }
            stdItem.additionalFields = additionalFields
            standardOrderItems.append(stdItem)

        empty_addr = Address(name1="", name2="", name3="",
                                  street1="", zipCode="", city="", province="",
                                  email="", telephone="", mobile="")

        try:
            if 'ShippingAddress' in order['order'].keys() and order['order']['ShippingAddress']:
                amazonAddr = AmazonAddress.parse_obj(order['order']['ShippingAddress'])
                shipAddress = self.__amazon_to_standard_address(amazonAddr)
            else:
                shipAddress = empty_addr
        except Exception as e:
            logger.warning(f"Error parsing shipping address for order [{orderId}]: {e}, Error Type: {type(e).__name__}")
            shipAddress = empty_addr

        shipAddress.email = jsonpath(order, '$.order.BuyerInfo.BuyerEmail', "")
        additionalFields = {}
        orderStatus = order['order']['OrderStatus']
        standardOrder = StandardOrder(orderId=orderId,
                                      sellerId=order['account_id'],
                                      salesChannel="SalesChannel",
                                      createdAt=order['order']['PurchaseDate'],
                                      updatedAt=order['order']['LastUpdateDate'],
                                      purchasedAt=order['order']['PurchaseDate'],
                                      status=orderStatus,
                                      items=standardOrderItems,
                                      shipAddress=shipAddress,
                                      billAddress=None,
                                      additionalFields=additionalFields,
                                      # trackIds=None,
                                      # parcelNumbers=None
                                      )
        additionalFields['isTransparency'] = self.need_transparency_code(standardOrder)
        return standardOrder

    def need_transparency_code(self, order: StandardOrder):
        for item in order.items:
            if item.additionalFields.get('isTransparency', False):
                return True
        return False

    def get_unshipped_orderlines(self, days_ago=7, up_to_date=True) -> List[OrderItem]:
        """
        Get all FBM orderlines within the specified time range via Amazon API, and save them to MongoDB.
        The function will return a list of up-to-date FBM orderlines.
        :param days_ago: Number of days to fetch orders from
        :return: List of up-to-date FBM orderlines
        """
        orders = self.find_unshipped_orders(days_ago=days_ago, up_to_date=up_to_date)
        orderlines = []
        for order in orders:
            orderlines += order.items
        sortedOrderlines = sorted(orderlines, key=lambda x: x.sku)
        return sortedOrderlines

    def get_daily_mfn_sales(self, days_ago=7) -> List[dict]:
        """
        Get daily MFN sales within the specified time range.
        TODO: 从每天几点开始统计，而不是从每天0点开始统计？
        :param days_ago:  Number of days to fetch orders from.
        :return:
        """
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
            {'$sort': {'sellerSKU': 1}},
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
        mdb_orders_collection: Collection = self.db_client[self.db_name][self.db_collection]
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

    def __init__(self, key_index: int,
                 marketplace: Marketplaces, ):
        super().__init__()
        self.db_name = "amazon_data"
        self.db_collection = "catalog"
        self.marketplace: Marketplaces = marketplace
        if key_index is not None:
            api_key = AmazonSpAPIKey.from_json(key_index)
            self.api = AmazonCatalogAPI(api_key=api_key, marketplace=marketplace)


    def save_catalog(self, asin):
        """
        Fetch the catalog item from Amazon API and save it to MongoDB. If the catalog item already exists in MongoDB, update it.
        If the catalog item does not exist in MongoDB, insert it.
        :param asin:
        :return:
        """
        mdb_catalog_collection = self.db_client[self.db_name][self.db_collection]
        # Find the catalog item in MongoDB
        item = mdb_catalog_collection.find_one({"_id": asin})
        # If the catalog item does not exist in MongoDB, fetch it from Amazon API
        if item is None:
            logger.info(f"Detected new catalog item [{asin}]...")
            item = self.api.get_catalog_item(asin)
            time.sleep(1)
        # There is a 10% chance to fetch from API and update database
        else:
            if random() < 0.01:
                logger.info(f"Random selected catalog item [{asin}] to fetch again...")
                item = self.api.get_catalog_item(asin)
                time.sleep(1)
            else:
                item = item['catalogItem']

        # if item has no attribute "AttributeSets"
        if 'AttributeSets' not in item.keys():
            return None

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
        """
        Fetch all catalog items from Amazon API and save them to MongoDB.
        :return: None
        """
        # Get all ASINs from orders collection
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

        # Fetches catalog items from Amazon API and saves them to MongoDB
        for asin in asinList:
            self.save_catalog(asin)

    def get_catalog_item(self, asin):
        """
        Get the catalog item from MongoDB.
        :param asin:  ASIN of the catalog item
        :return:  The catalog item as a dictionary, or None if not found.
        """
        mdb_catalog_collection: Collection = self.db_client[self.db_name][self.db_collection]
        item = mdb_catalog_collection.find_one({"_id": asin})
        if item is None:
            logger.info(f"Catalog item [{asin}] not found in MongoDB...")
            return None
        else:
            return item['catalogItem']

    def get_all_catalog_items(self):
        """
        Get all catalog items from MongoDB.
        :return:  A list of all catalog items as dictionaries.
        """
        mdb_catalog_collection: Collection = self.db_client[self.db_name][self.db_collection]
        items = mdb_catalog_collection.find()
        return list(items)

