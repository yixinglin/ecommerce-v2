from typing import List

from pymongo.collection import Collection

from core.db import OrderMongoDBDataManager, MongoDBDataManager
from core.log import logger
from external.amazon import AmazonAddress
from models.orders import StandardOrder, OrderItem
from models.shipment import Address
from utils.stringutils import jsonpath, isEmpty


class AmazonOrderMongoDB(OrderMongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "amazon_data"
        self.db_collection_name = "orders"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_orders(self, offset: int = 0,
                     limit: int = 100, *args, **kwargs) -> List[StandardOrder]:
        """
                Find orders in MongoDB.

                @Note: This function is a low-level function. Do not modify without proper review.

                :param kwargs: filter conditions
                :return:
                Example:
                find_orders(filter={"order.OrderStatus": "Unshipped", "order.FulfillmentChannel": "MFN"})
                """
        orders_collection: Collection = self.db_client[self.db_name][self.db_collection_name]
        results = list(orders_collection.find(**kwargs)
                       .sort({"order.PurchaseDate": -1})
                       .skip(offset)
                       .limit(limit)
                       )
        results = [self.to_standard_order(r) for r in results]
        return results

    def query_order_by_id(self, id: str, *args, **kwargs) -> StandardOrder:
        result = self.query_orders_by_ids([id])
        return result[0] if result else None

    def query_orders_by_ids(self, ids: str, *args, **kwargs) -> List[StandardOrder]:
        filter_ = {"_id": {"$in": ids}}
        orders = list(self.query_orders(filter=filter_, limit=len(ids)))
        # Sort the orders by the given order IDs
        if len(orders) > 0:
            order_dict = {order.orderId: order for order in orders}
            orders = [order_dict[id] for id in ids]
        return orders

    def save_order(self, order_id, document):
        mdb_orders_collection = self.db_client[self.db_name][self.db_collection_name]
        # Update the order if it already exists, otherwise insert it
        result = (mdb_orders_collection.update_one(
            {"_id": order_id},
            {"$set": document},
            upsert=True)
        )
        return result

    def update_order(self, order: StandardOrder) -> StandardOrder:
        raise NotImplementedError()

    def delete_order(self, id: str) -> bool:
        raise NotImplementedError()

    @staticmethod
    def need_transparency_code(order: StandardOrder):
        for item in order.items:
            if item.additionalFields.get('isTransparency', False):
                return True
        return False

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
                                      sellerId=order.get("account_id", "Unknown"),
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



class AmazonCatalogMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "amazon_data"
        self.db_collection = "catalog"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection]

    def query_catalog_item(self, asin: str) -> dict:
        catalog_collection = self.get_db_collection()
        item = catalog_collection.find_one({"_id": asin})
        if item is None:
            logger.warning(f"Catalog item [{asin}] not found in MongoDB...")
            return None
        else:
            return item

    def delete_catalog_item(self, asin: str) -> bool:
        catalog_collection = self.get_db_collection()
        result = catalog_collection.delete_one({"_id": asin})
        if result.deleted_count == 1:
            return True
        else:
            return False

    def save_catalog(self, asin: str, document: dict):
        catalog_collection = self.get_db_collection()
        return catalog_collection.update_one(
            {"_id": asin},
            {"$set": document},
            upsert=True
        )


