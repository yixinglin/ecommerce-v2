import time
from datetime import datetime, timedelta
from random import random
from typing import List, Dict, Set
from sp_api.base import Marketplaces, SellingApiRequestThrottledException
from core.db import OrderQueryParams, RedisDataManager
from core.exceptions import DimensionNotFoundException
from core.log import logger
from crud.amazon import AmazonOrderMongoDB, AmazonCatalogMongoDB
from models.orders import StandardOrder, OrderStatus
from models.shipment import Address
from schemas.amazon import DailyShipment, DailySalesCountVO, PackageDimensions, CatalogAttributes
from services.amazon.base import standard_to_amazon_address
from external.amazon import AmazonSpAPIKey, AmazonOrderAPI, AmazonCatalogAPI
from external.amazon import DATETIME_PATTERN, now
import utils.time as time_utils
from services.amazon.bulkOrderService import AmazonBulkPackSlipDE

"""
# Class Dependency 
AmazonService
    - AmazonOrderService
    - AmazonCatalogService

"""

# https://developer-docs.amazon.com/sp-api/docs/orders-api-v0-reference#updateshipmentstatus

MAP_ORDER_STATUS = {
    "Pending": OrderStatus.pending.value,
    "Unshipped": OrderStatus.confirmed.value,
    "Shipped": OrderStatus.shipped.value,
    "Canceled": OrderStatus.cancelled.value,
}


class AmazonOrderService:
    """
    This class is used to manage Amazon orders in MongoDB.
    """
    FILTER_01 = {"order.OrderStatus": "Unshipped",
                 "order.FulfillmentChannel": "MFN"}

    def __init__(self, key_index: int,
                 marketplace: Marketplaces, *args, **kwargs):
        """
         Initialize the AmazonOrderMongoDBManager.
        :param db_host: Host of the MongoDB server.
        :param db_port:   Port of the MongoDB server.
        :param key_index:  Index of the API key to use.
        :param marketplace:  e.g. Marketplaces.DE
        """
        super().__init__(*args, **kwargs)
        self.mdb = AmazonOrderMongoDB()
        self.marketplace = marketplace
        self.fulfillment_channels = ["MFN"]
        if key_index is not None:
            api_key = AmazonSpAPIKey.from_json(key_index)
            self.api = AmazonOrderAPI(api_key=api_key, marketplace=marketplace)
            self.account_id = api_key.account_id
            self.salesChannel = self.api.salesChannel

    def __enter__(self):
        self.mdb.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mdb.close()

    def need_update(self, order: dict) -> bool:
        """
        Check if the order needs to be updated.
        :param order: Fetched order from Amazon API
        :return:
        """
        # Check if the order already exists in MongoDB
        order_id = order["AmazonOrderId"]
        order_from_db = self.mdb.get_db_collection().find_one({"_id": order_id})
        # order_from_db = self.mdb.find_order_by_id(order_id)
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
        if order is None:  # Fetch the order from Amazon API if not provided
            order = self.api.fetch_order(order_id).payload
            time.sleep(0.5)  # Wait for 1 second to avoid throttling

        order_items = self.api.fetch_order_items(order_id).payload
        time.sleep(0.7)  # Wait for 1 second to avoid throttling

        # Store the shipping address in a temporary variable
        ship_addr_from_api = order.get('ShippingAddress', None)
        if ship_addr_from_api is None:
            # The api does not return a shipping address
            order['ShippingAddress'] = ship_addr_from_api

        # Query the order data from MongoDB
        order_from_db = self.mdb.get_db_collection().find_one({"_id": order_id})
        if order_from_db:
            shipping_address = order_from_db['order'].get('ShippingAddress', None)
            if shipping_address is None or len(shipping_address.keys()) <= 4:
                # The shipping address is not complete, update it with the API data
                order['ShippingAddress'] = ship_addr_from_api
            elif len(shipping_address.keys()) > 4:
                # The shipping address is complete, do not update it with the API data
                order['ShippingAddress'] = shipping_address
        else:
            # Do nothing, if the order data does not exist in MongoDB
            pass

        document = {
            "_id": order_id,
            "order": order,
            "items": order_items,
            "account_id": self.api.get_account_id(),
            "fetchedAt": now()
        }

        # Update the order if it already exists, otherwise insert it
        return self.mdb.save_order(order_id, document)

    def add_shipping_address_to_order(self, order_id: str, shipping_address: Address) -> bool:
        """
        Add shipping address to an order in MongoDB.
        :param order_id: Amazon order ID
        :param shipping_address: Shipping address to add to the order
        Doc: https://developer-docs.amazon.com/sp-api/docs/orders-api-v0-reference#address
       """
        amazonAddress = standard_to_amazon_address(shipping_address)
        ship_addr = amazonAddress.dict()
        mdb_orders_collection = self.mdb.get_db_collection()
        # Check if the order has been stored in MongoDB
        order_from_db = self.mdb.query_order_by_id(order_id)

        if order_from_db:  # Order already exists in MongoDB
            # Update the order with the shipping address
            result = (mdb_orders_collection.update_one(
                {"_id": order_id},
                {"$set": {"order.ShippingAddress": ship_addr}},
                upsert=True)
            )
        else:
            # Fetch the order from Amazon API and add the shipping address
            order = self.api.fetch_order(order_id).payload
            order['ShippingAddress'] = ship_addr
            # Save the order to MongoDB
            result = self.save_order(order_id, order=order)
        return result

    # def add_pack_slip_to_order(self, order_id: str, pack_slip: str):
    #     """
    #     Add pack slip to an order in MongoDB.
    #     :param order_id:
    #     :param pack_slip:
    #     :return:
    #     """
    #     # Check if the order has been stored in MongoDB
    #     order_from_db = self.mdb.query_order_by_id(order_id)
    #     # if order dose not exist in MongoDB, fetch the order from Amazon API and add the pack slip
    #     if not order_from_db:
    #         order = self.api.fetch_order(order_id).payload
    #         self.save_order(order_id, order=order)
    #
    #     # Update the order with the pack slip
    #     mdb_orders_collection = self.mdb.get_db_collection()
    #     result = (mdb_orders_collection.update_one(
    #         {"_id": order_id},
    #         {"$set": {"packslip": pack_slip}},
    #         upsert=True)
    #     )
    #
    #     return result

    def save_all_orders(self, days_ago=30, **kwargs):
        """
        Save all orders within the specified time range to MongoDB.
        :param days_ago: Number of days to fetch orders from
        :param kwargs: Additional filters for the orders, e.g. FulfillmentChannels=["MFN"]
        :return:
        Example:
        save_all_orders(days_ago=30, FulfillmentChannels=["MFN"])
        """
        orders = self.api.fetch_all_orders(days_ago=days_ago, **kwargs)
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
        :param kwargs: filter conditions
        Example:
        find_orders(filter={"order.OrderStatus": "Unshipped", "order.FulfillmentChannel": "MFN"})
        """
        return self.mdb.query_orders(offset=offset, limit=limit,
                                     **kwargs)

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
        :param ids:
        :return:
        """
        return self.mdb.query_orders_by_ids(ids)

    def find_order_by_id(self, order_id: str) -> StandardOrder:
        """
        Find an order by ID in MongoDB.
        :param order_id:
        :return:
        """
        return self.mdb.query_order_by_id(order_id)

    def find_unshipped_orders(self) -> List[StandardOrder]:
        """
        Get all FBM orders within the specified time range via Amazon API, and save them to MongoDB.
        The function will return a list of up-to-date FBM orders.
        :param days_ago: Number of days to fetch orders from
        :return: List of up-to-date FBM orders
        """
        # Get all FBM orders within the specified time range
        filter_ = {
            "order.FulfillmentChannel": "MFN",
            "order.OrderStatus": "Unshipped",
        }
        if hasattr(self, 'account_id'):
            filter_['account_id'] = self.account_id
        if hasattr(self, 'salesChannel'):
            filter_['order.SalesChannel'] = self.salesChannel
        orders = self.find_orders(filter=filter_)
        return orders

    def find_all_asin(self, days_ago=30) -> Set[str]:
        """
        Get all ASINs from all FBM orders within the specified time range in MongoDB.
        :param days_ago:
        :return:
        """
        params = OrderQueryParams()
        params.purchasedDateFrom = time_utils.days_ago(days_ago)
        orders = self.find_orders_by_query_params(params)
        asin = set()
        for order in orders:
            for item in order.items:
                asin.add(item.asin)
        return asin

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
        # mdb_orders_collection: Collection = self.db_client[self.db_name][self.db_collection]
        mdb_orders_collection = self.mdb.get_db_collection()
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


class AmazonCatalogService:

    def __init__(self, key_index: int,
                 marketplace: Marketplaces, ):
        # self.db_name = "amazon_data"
        # self.db_collection = "catalog"
        self.mdb = AmazonCatalogMongoDB()
        self.marketplace: Marketplaces = marketplace
        if key_index is not None:
            api_key = AmazonSpAPIKey.from_json(key_index)
            self.api = AmazonCatalogAPI(api_key=api_key, marketplace=marketplace)

    def __enter__(self):
        self.mdb.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mdb.close()

    def save_catalog(self, asin, force_fetch=False):
        """
        Fetch the catalog item from Amazon API and save it to MongoDB. If the catalog item already exists in MongoDB, update it.
        If the catalog item does not exist in MongoDB, insert it.
        :param asin:
        :return:
        """
        # Find the catalog item in MongoDB
        item = self.mdb.query_catalog_item(asin)
        is_random_fetch = random() < 0.01
        # Fetch catalog from Amazon API, if
        # force_fetch is set,
        # the catalog item does not exist in MongoDB,
        # random() < 0.01
        if force_fetch or item is None or is_random_fetch:
            logger.info(f"Fetching catalog item [{asin}]... is_random_fetch={is_random_fetch}")
            item = self.api.fetch_catalog_item(asin)
            # TODO: If catalog item is None, log error and return None. Delete the item from MongoDB if it exists.
            fetchedAt = now()
            time.sleep(1)
        else:
            item = item['catalogItem']
            fetchedAt = item.get('fetchedAt', None)

        # if item has no attribute "AttributeSets"
        if 'AttributeSets' not in item.keys():
            return None

        document = {
            "_id": asin,
            "fetchedAt": fetchedAt,
            "catalogItem": item,
        }

        return self.mdb.save_catalog(asin, document)

    def query_catalog_item(self, asin):
        """
        Get the catalog item from MongoDB.
        :param asin:  ASIN of the catalog item
        :return:  The catalog item as a dictionary, or None if not found.
        """
        return self.mdb.query_catalog_item(asin)

    def query_all_catalog_items(self):
        """
        Get all catalog items from MongoDB.
        :return:  A list of catalog items as dictionaries.
        """
        return self.mdb.query_all_catalog_items()

    def remove_catalog_item(self, asin):
        """
        Remove the catalog item from MongoDB.
        """
        return self.mdb.delete_catalog_item(asin)

    def create_asin_image_url_dict(self) -> Dict[str, str]:
        """
        Get a dictionary of ASINs and their image URLs.
        :return:  A dictionary of ASINs and their image URLs.
        """
        # Query all catalog items
        mdb_catalog_collection = self.mdb.get_db_collection()
        catalog_items = mdb_catalog_collection.find()
        result = {}
        for item in catalog_items:
            asin = item['_id']
            try:
                result[asin] = item['catalogItem']['AttributeSets'][0]['SmallImage']['URL']
            except KeyError as e:
                logger.error(f"Error while getting ASIN image URL for {asin}")
                self.remove_catalog_item(asin)
        return result

    def query_all_asins_from_db(self) -> List[str]:
        items = self.query_all_catalog_items()
        asin_set = set([item['_id'] for item in items])
        return list(asin_set)


class AmazonService:

    def __init__(self, key_index: int,
                 marketplace: Marketplaces):
        """
        This class provides a high-level interface for fetching and manipulating Amazon orders.
        It handles business logic based on the user requests.
        :param key_index:  Index of the API key to use.
        :param marketplace:  Marketplace to use.
        """

        self.catalog_service = AmazonCatalogService(key_index, marketplace)
        self.order_service = AmazonOrderService(key_index, marketplace)
        self.api = self.order_service.api
        self.fulfillment_channels = self.order_service.fulfillment_channels
        self.marketplace = marketplace

    def __enter__(self):
        self.catalog_service.__enter__()
        self.order_service.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.catalog_service.__exit__(exc_type, exc_val, exc_tb)
        self.order_service.__exit__(exc_type, exc_val, exc_tb)

    def sum_daily_ordered_items(self, days_ago=7, up_to_date=False):
        """
        Get the total number of ordered items for each day.
        """
        daily = self.order_service.get_daily_mfn_sales(days_ago=days_ago)
        # Convert daily-sales data to DailySalesCountVO objects
        daily_sales_vo = []
        for day in daily:
            # Convert dailyShipments JSON array to list of DailyShipment objects
            daily_shipments = [DailyShipment(**item) for item in day['dailyShipments']]
            # Create DailySalesCountVO object
            vo = DailySalesCountVO(purchaseDate=day['purchaseDate'],
                                   hasUnshippedOrderItems=day['dailyShippedItemsCount'] < day['dailyOrdersItemsCount'],
                                   dailyShippedItemsCount=day['dailyShippedItemsCount'],
                                   dailyOrdersItemsCount=day['dailyOrdersItemsCount'],
                                   dailyShipments=daily_shipments)
            daily_sales_vo.append(vo)

        asin_image_url = self.catalog_service.create_asin_image_url_dict()
        for day in daily_sales_vo:
            for shipment in day.dailyShipments:
                shipment.imageUrl = asin_image_url.get(shipment.asin, "")
        return daily_sales_vo

    def query_amazon_orders(self, days_ago, status, offset, limit, up_to_date=False):
        """
        Query an Amazon orders.
        """
        if up_to_date:
            self.order_service.save_all_orders(days_ago=days_ago, FulfillmentChannels=self.fulfillment_channels)

        purchasedDateFrom = time_utils.days_ago(days_ago)
        params = OrderQueryParams()
        params.purchasedDateFrom = purchasedDateFrom
        params.status = status
        params.offset = offset
        params.limit = limit

        orders = self.order_service.find_orders_by_query_params(params)
        lengthOrders = len(orders)
        start = 0
        end = 0
        if lengthOrders > 0:
            start = offset
            end = min(len(orders), offset + limit)
            orders = orders[start:end]

        # Add image URL to each order item
        asin_to_image_url = self.catalog_service.create_asin_image_url_dict()
        for od in orders:
            for odline in od.items:
                odline.image = asin_to_image_url.get(odline.asin, "")

        # TODO Add tracking id to each order
        return {"orders": orders,
                "api_client": self.api.get_account_id(),
                "offset": offset,
                "limit": limit,
                "length": end - start,
                "size": lengthOrders
                }

    def query_unshipped_amazon_orders(self, days_ago=7, up_to_date=False):
        """
        Query unshipped Amazon orders.
        """
        if up_to_date:
            # Fetch latest orders if up-to-date flag is set
            self.order_service.save_all_orders(days_ago=days_ago, FulfillmentChannels=self.fulfillment_channels)
        orders = self.order_service.find_unshipped_orders()
        return {
            "orders": orders,
            "api_client": self.api.get_account_id(),
            "length": len(orders)
        }

    def query_unshipped_order_numbers(self, days_ago=7, up_to_date=False):
        data = self.query_unshipped_amazon_orders(days_ago=days_ago, up_to_date=up_to_date)
        orders = data["orders"]
        order_numbers = [order.orderId for order in orders]
        return {"orderNumbers": order_numbers, "upToDate": up_to_date,
                "api_client": self.api.get_account_id(),
                "length": len(order_numbers)
                }

    def parse_amazon_pack_slip_page(self, pack_slip_page, format_="json"):
        """
        Parse Amazon pack slip page.
        :param pack_slip_page:
        :return:
        """
        if self.marketplace == Marketplaces.DE:
            proc = AmazonBulkPackSlipDE(pack_slip_page)
            orders_: List[StandardOrder] = proc.extract_all()
            orders = orders_ if format_ == "json" or format_ == "csv" else AmazonBulkPackSlipDE(
                pack_slip_page).extract_all(
                format=format_)
            proc.make_page_map()  # Cache packing slip data to Redis for 12 hours.
            for order_ in orders_:
                self.order_service.add_shipping_address_to_order(order_.orderId, order_.shipAddress)
        else:
            raise RuntimeError(f"Unsupported marketplace [{self.marketplace}]")
        return {
            "orders": orders,
            "formatIn": format_,
            "formatOut": format_,
            "message": f"{len(orders)} addresses have been successfully parsed from the packing slip and saved to the "
                       f"database.",
            "length": len(orders),
        }

    def save_all_catalogs_from_orders(self):
        """
        Fetch all catalog items from Amazon API and save them to MongoDB.
        :return: None
        """
        asin_set = self.order_service.find_all_asin(days_ago=30)
        # Fetches catalog items from Amazon API and saves them to MongoDB
        for asin in list(asin_set):
            self.catalog_service.save_catalog(asin)

    def save_all_catalogs_from_db(self, force_fetch=False):
        asin_set = self.catalog_service.query_all_asins_from_db()
        for asin in asin_set:
            self.catalog_service.save_catalog(asin, force_fetch=force_fetch)
            if force_fetch:
                time.sleep(2)

    def clear_expired_catalogs(self):
        """
        TODO: Remove all expired catalog items from MongoDB.
        :return: None
        """
        # Find all ASINs of catalog items that are not sold for n days
        asin_set = self.order_service.find_all_asin(days_ago=120)
        # Query all catalog items from MongoDB
        items = self.catalog_service.query_all_catalog_items()
        # Remove all catalog items that are not sold for n days
        asin_set_in_db = set([item['_id'] for item in items])
        for asin in asin_set_in_db - asin_set:
            self.catalog_service.remove_catalog_item(asin)

    def get_catalog_attributes(self, asin):
        """
        Get the catalog attributes of an ASIN.
        :param asin:  ASIN of the catalog item.
        :return:  The catalog attributes as a dictionary, or None if not found.
        """
        item = self.catalog_service.query_catalog_item(asin)
        if item is None:
            raise RuntimeError(f"Catalog item [{asin}] not found in Database.")
        attribute_set = item['catalogItem']['AttributeSets'][0]

        if 'PackageDimensions' not in attribute_set and 'ItemDimensions' not in attribute_set:
            raise DimensionNotFoundException(f"Asin [{asin}] has no PackageDimensions or ItemDimensions")

        pdim = {} if 'PackageDimensions' not in attribute_set else attribute_set['PackageDimensions']
        idim = {} if 'ItemDimensions' not in attribute_set else attribute_set['ItemDimensions']
        pdim.update(idim)

        # Standardize data
        zero_inch = {"value": 0, "Units": "inches"}
        zero_pound = {"value": 0, "Units": "pounds"}
        length = pdim['Length'] if "Length" in pdim else zero_inch
        width = pdim['Width'] if "Width" in pdim else zero_inch
        height = pdim['Height'] if "Height" in pdim else zero_inch
        weight = pdim['Weight'] if "Weight" in pdim else zero_pound

        dim = dict()
        if length["Units"] == "inches":  # Inches to millimeters
            dim["length"] = round(length["value"] * 25.4)
            dim["width"] = round(width["value"] * 25.4)
            dim["height"] = round(height["value"] * 25.4)
        else:
            raise ValueError(f"Unsupported unit [{length['Units']}]")

        if weight["Units"] == "pounds":  # pounds to grams
            dim["weight"] = round(weight["value"] * 453.592)
        else:
            raise ValueError(f"Unsupported unit [{weight['Units']}]")

        package_dimensions = PackageDimensions(**dim)
        attr = dict()
        attr["asin"] = asin
        attr["seller_sku"] = "unknown"
        attr["brand"] = attribute_set['Brand']
        attr["title"] = attribute_set['Title']
        attr["image_url"] = attribute_set['SmallImage']['URL']
        attr["package_dimensions"] = package_dimensions
        attribute_set = CatalogAttributes(**attr)
        return attribute_set


class FbaService:

    def __init__(self):
        self.redis_manager = RedisDataManager()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fba_packing_rule(self, shipment_qty, sku, ctn_capacity) -> Dict:
        """
        计算FBA装箱规则
        :param shipment_qty: 发货数量
        :param sku: SKU名称
        :param ctn_capacity: 大箱容量
        :return: 装箱描述，空间利用率数组
        """
        full_ctns = shipment_qty // ctn_capacity  # 计算完整大箱数量
        remainder = shipment_qty % ctn_capacity  # 计算余数

        packing_description = []
        utilization_rates = []

        # 记录完整大箱的装箱情况
        if full_ctns > 0:
            packing_description.append(f"{full_ctns * ctn_capacity}x ({sku}) = {full_ctns} Ctn")
            utilization_rates.extend([100] * full_ctns)

        # 处理余数部分
        if remainder > 0:
            if remainder >= 0.5 * ctn_capacity:  # 超过50%时，仍然使用大箱
                packing_description.append(f"{remainder}x ({sku}) = 1 Ctn")
                utilization_rates.append(round((remainder / ctn_capacity) * 100, 2))
            else:  # 低于50%时，使用小箱
                packing_description.append(f"{remainder}x ({sku}) = 1 Ctn-S")
                utilization_rates.append(round((remainder / (0.5 * ctn_capacity)) * 100, 1))
        return {
            "desc": packing_description,
            "utiliz_rates": utilization_rates
        }

    def cache_fba_max_ctn_capacity(self, sku, ctn_capacity):
        """
        缓存FBA装箱规则
        :param sku: SKU名称
        :param ctn_capacity: 大箱容量
        :return: 装箱描述，空间利用率数组
        """
        mapping = {
            "sku": sku,
            "ctn_capacity": ctn_capacity
        }
        three_months = 3 * 30 * 24 * 60 * 60
        self.redis_manager.set_json(f"FBA_MAX_CTN:{sku}", mapping, three_months)

    def get_fba_max_ctn_capacity(self, sku) -> dict:
        """
        获取FBA最大箱容量
        :param sku: SKU名称
        :return: 最大箱容量
        """
        return self.redis_manager.get_json(f"FBA_MAX_CTN:{sku}")


    def delete_fba_max_ctn_capacity(self, sku):
        """
        删除FBA最大箱容量缓存
        :param sku: SKU名称
        :return: None
        """
        self.redis_manager.delete(f"FBA_MAX_CTN:{sku}")
