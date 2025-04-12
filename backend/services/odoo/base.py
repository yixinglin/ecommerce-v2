import base64
import os
import time
from typing import List

from pydantic import BaseModel

from core.log import logger
from crud.odoo import (OdooQuantMongoDB,
                       OdooStorageLocationMongoDB,
                       OdooPutawayRuleMongoDB,
                       OdooProductTemplateMongoDB, OdooContactMongoDB, OdooProductMongoDB, OdooPackagingMongoDB,
                       OdooOrderlineMongoDB)
from external.odoo import OdooAPIKey, OdooInventoryAPI, OdooProductAPI, OdooContactAPI
from external.odoo import DATETIME_PATTERN as ODOO_DATETIME_PATTERN
import utils.time as time_utils
from external.odoo.order import OdooOrderAPI
from external.odoo.product import OdooProductPackagingAPI
from models import Address
from models.orders import StandardProduct
from models.warehouse import Quant, PutawayRule
import re
import random

from utils import stringutils


# def need_to_fetch(query_mothed, id, current_write_date: str):
#     """
#     Check if the record in DB needs to be fetched again.
#     The record needs to be fetched if it is not found in DB or
#     if the last write date is different from the current write date.
#     :param query_mothed: A callback function of a query method of the DB
#     :param id: The id of the record in Odoo
#     :param current_write_date: The current write date of the record in Odoo
#     :return:  True if the record needs to be fetched, False otherwise
#     """
#     is_readom_fetch = random.random() < 0.01
#     # 0.01 is the probability of fetching the record from Odoo API
#
#     item = query_mothed(id)
#     if item is None or is_readom_fetch:
#         # Do not find the record in DB, need to fetch it
#         if is_readom_fetch:
#             logger.info(f"Fetching randomly with id = {id}...")
#         else:
#             logger.info(f"Fetching new data with id = {id}...")
#         return True
#     else:
#         last_write_date = item['data']['write_date']
#         if last_write_date != current_write_date:
#             # The record in DB is outdated, need to fetch it
#             return True
#         else:
#             # The record in DB is up-to-date, no need to fetch it
#             return False


def need_to_fetch(query_method, record_id, current_write_date: str):
    """
    判断是否需要从 Odoo 再次获取数据：
      1. 在数据库中没有查到该记录时；
      2. 随机抽取到一定概率时（此处为 1%）；
      3. 数据库中的 write_date 与当前 Odoo 的 write_date 不一致时。

    :param query_method: 数据库查询回调函数
    :param record_id:    Odoo 记录的 ID
    :param current_write_date: Odoo 中当前记录的 write_date
    :return: 需要抓取则返回 True，否则返回 False
    """
    is_random_fetch = (random.random() < 0.01)
    item = query_method(record_id)

    # 随机概率或数据库中不存在该记录：直接需要再次抓取
    if is_random_fetch or not item:
        logger.info(f"Fetching {'randomly' if is_random_fetch else 'new data'} with id = {record_id}...")
        return True

    # 数据库中已经有记录，但 write_date 不一致，需要更新
    return item['data']['write_date'] != current_write_date


def save_record(fetch_object_ids, fetch_write_date,
                query_object_by_id, object_name, save_object, include_inactive=False):
    """
    Save records from Odoo API to MongoDB if the record has changed since last fetch.

    :param fetch_object_ids: A callback function of a fetch method of the Odoo API
    :param fetch_write_date: A callback function of a fetch method of the Odoo API
    :param query_object_by_id: A callback function of a query method of the MongoDB
    :param object_name: The name of the object to be saved
    :param save_object: A callback function of a save method of the MongoDB
    """
    if include_inactive:
        domain = [("active", "in", [True, False])]
    else:
        domain = []
    object_ids = fetch_object_ids(domain)  # Fetch object ids from Odoo API
    write_dates = fetch_write_date(object_ids)  # Fetch write dates from Odoo API
    dic_write_dates = {item['id']: item['write_date']
                       for item in write_dates}
    uni_ids = dic_write_dates.keys()  # Unique ids
    for id in uni_ids:
        current_write_date = dic_write_dates[id]
        if need_to_fetch(query_object_by_id, id, current_write_date):
            # Save object if the record has changed since last fetch
            logger.info(f"Saving {object_name} with id = {id}")
            save_object(id)


def convert_datetime_to_utc_format(odoo_datetime: str):
    datetime_obj = time_utils.str_to_datatime(odoo_datetime, ODOO_DATETIME_PATTERN)
    return time_utils.datetime_to_str(datetime_obj, time_utils.DATETIME_PATTERN)


def get_field_value(data, field_name):
    # Get the value of a field in a dictionary, return None if the value is False
    val = data.get(field_name, "")
    if (val is not None and val == False):
        return ""
    return val


class OdooInventoryServiceBase:

    def __init__(self, key_index, *args, **kwargs):
        self.key_index = key_index
        self.mdb_location = OdooStorageLocationMongoDB()
        self.mdb_quant = OdooQuantMongoDB()
        self.mdb_putaway_rule = OdooPutawayRuleMongoDB()
        if key_index is not None:
            api_key = OdooAPIKey.from_json(key_index)
            self.api = OdooInventoryAPI(api_key, **kwargs)
            self.alias = self.api.get_alias()
            self.username = self.api.get_username()
            logger.info(f"Odoo username: {self.username} ({self.alias})")

    def __enter__(self):
        self.mdb_location.connect()
        client = self.mdb_location.get_client()
        self.mdb_quant.set_client(client)
        self.mdb_putaway_rule.set_client(client)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mdb_location.close()

    def save_location(self, location_id):
        results = self.api.fetch_location_by_ids([location_id])
        if results is None or len(results) == 0:
            logger.error(f"Failed to fetch location with id = {location_id}")
            return None
        item_data = results[0]
        fetchedAt = time_utils.now()
        create_date = convert_datetime_to_utc_format(item_data['create_date'])
        time.sleep(0.2)

        document = {
            '_id': location_id,
            'fetchedAt': fetchedAt,
            'createdAt': create_date,
            'data': item_data,
            'alias': self.api.get_alias()
        }
        logger.info(f"Saving location [{location_id}] {item_data['complete_name']}...")
        return self.mdb_location.save_storage_location(location_id, document)

    def save_quant(self, quant_id):
        results = self.api.fetch_quant_by_ids([quant_id])
        if results is None or len(results) == 0:
            logger.error(f"Failed to fetch quant with id = {quant_id}")
            return None
        item_data = results[0]
        fetchedAt = time_utils.now()
        create_date = convert_datetime_to_utc_format(item_data['create_date'])
        time.sleep(0.2)
        document = {
            '_id': quant_id,
            'fetchedAt': fetchedAt,
            'createdAt': create_date,
            'data': item_data,
            'alias': self.api.get_alias()
        }
        return self.mdb_quant.save_quant(quant_id, document)

    def save_putaway_rule(self, putaway_rule_id: int):
        results = self.api.fetch_putaway_rule_by_ids([putaway_rule_id])
        if results is None or len(results) == 0:
            logger.error(f"Failed to fetch putaway rule with id = {putaway_rule_id}")
            return None
        item_data = results[0]
        fetchedAt = time_utils.now()
        create_date = convert_datetime_to_utc_format(item_data['create_date'])
        time.sleep(0.2)

        document = {
            '_id': putaway_rule_id,
            'fetchedAt': fetchedAt,
            'createdAt': create_date,
            'data': item_data,
            'alias': self.api.get_alias()
        }
        return self.mdb_putaway_rule.save_putaway_rule(putaway_rule_id, document)

    def to_standard_quant(self, quant) -> Quant:
        data = quant['data']
        fullname = data['product_id'][1]
        pattern = r"\[([A-Z0-9\-]+)\]\s(.+)"
        match = re.match(pattern, fullname)
        if match:
            reference_code = match.group(1)
            product_name = match.group(2)
        else:
            reference_code = ""
            product_name = fullname

        split_location_name = data['location_id'][1].split('/')
        if len(split_location_name) > 2:
            location_name = split_location_name[-1]
        else:
            location_name = data['location_id'][1]

        last_count_date = data['last_count_date']
        if last_count_date == False:
            last_count_date = ""
        else:
            last_count_date = last_count_date + " 00:00:00"
            last_count_date = convert_datetime_to_utc_format(last_count_date)

        q = Quant(
            id=str(data['id']),
            productId=str(data['product_id'][0]),
            productName=product_name,
            productUom=data['product_uom_id'][1],
            sku=reference_code,
            quantity=int(data['quantity']),
            reservedQuantity=int(data['reserved_quantity']),
            availableQuantity=int(data['available_quantity']),
            inventoryQuantity=int(data['inventory_quantity']),
            inventoryQuantitySet=int(data['inventory_quantity_set']),
            locationName=location_name,
            locationId=str(data['location_id'][0]),
            locationCode="",
            warehouseId=str(data['warehouse_id'][0]),
            warehouseName=data['warehouse_id'][1],
            lastCountDate=last_count_date,
        )
        return q

    def to_standard_putaway_rule(self, rule) -> PutawayRule:
        data = rule['data']

        split_location_in_name = data['location_in_id'][1].split('/')
        if len(split_location_in_name) > 2:
            location_in_name = split_location_in_name[-1]
        else:
            location_in_name = data['location_in_id'][1]

        split_location_out_name = data['location_out_id'][1].split('/')
        if len(split_location_out_name) > 2:
            location_out_name = split_location_out_name[-1]
        else:
            location_out_name = data['location_out_id'][1]

        r = PutawayRule(
            id=str(data['id']),
            productId=str(data['product_id'][0]),
            productName=data['product_id'][1],
            locationInId=str(data['location_in_id'][0]),
            locationInName=location_in_name,
            locationInCode="",
            locationOutId=str(data['location_out_id'][0]),
            locationOutName=location_out_name,
            locationOutCode="",
            active=data['active'],
            priority=data['sequence'],
            company=data['company_id'][1],
        )
        return r


class OdooProductServiceBase:

    def __init__(self, key_index, *args, **kwargs):
        self.key_index = key_index
        self.mdb_product_templ = OdooProductTemplateMongoDB()
        self.mdb_product = OdooProductMongoDB()
        if key_index is not None:
            api_key = OdooAPIKey.from_json(key_index)
            self.api = OdooProductAPI(api_key, **kwargs)
            self.alias = self.api.get_alias()
            self.username = self.api.get_username()
            logger.info(f"Odoo username: {self.username} ({self.alias})")

    def __enter__(self):
        self.mdb_product_templ.connect()
        client = self.mdb_product_templ.get_client()
        self.mdb_product.set_client(client)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mdb_product_templ.close()

    def save_product_template(self, product_templ_id):
        results = self.api.fetch_product_templates_by_ids([product_templ_id])
        if results is None or len(results) == 0:
            logger.error(f"Failed to fetch product template with id = {product_templ_id}")
            return None
        item_data = results[0]
        fetchedAt = time_utils.now()
        create_date = convert_datetime_to_utc_format(item_data['create_date'])
        time.sleep(0.2)

        document = {
            '_id': product_templ_id,
            'fetchedAt': fetchedAt,
            'createdAt': create_date,
            'data': item_data,
            'alias': self.api.get_alias()
        }
        return self.mdb_product_templ.save_product_template(product_templ_id, document)

    def save_product(self, product_id):
        results = self.api.fetch_products_by_ids([product_id])
        if results is None or len(results) == 0:
            logger.error(f"Failed to fetch product with id = {product_id}")
            return None
        item_data = results[0]
        fetchedAt = time_utils.now()
        create_date = convert_datetime_to_utc_format(item_data['create_date'])
        time.sleep(0.2)

        document = {
            '_id': product_id,
            'fetchedAt': fetchedAt,
            'createdAt': create_date,
            'data': item_data,
            'alias': self.api.get_alias()
        }
        return self.mdb_product.save_product(product_id, document)

    def save_product_image(self, b64_image: str):
        mid = int(len(b64_image) / 2)
        md5 = stringutils.text_to_md5(b64_image[:256] + b64_image[mid - 256:mid + 256] + b64_image[-256:])
        filename = f"static2/images/{md5}.jpg"
        if os.path.exists(filename):
            return "/" + filename

        with open(filename, "wb") as f:
            f.write(base64.b64decode(b64_image))
        return "/" + filename

    def to_standard_product(self, product_data) -> StandardProduct:
        alias = product_data['alias']
        data = product_data['data']
        id = str(data['id'])
        fetchedAt = product_data['fetchedAt']
        additionalFields = {
            'alias': alias,
            'fetchedAt': fetchedAt
        }
        product = StandardProduct(
            id=id,
            name=data['name'],
            sku=get_field_value(data, 'default_code'),
            ean="",
            code=get_field_value(data, 'default_code'),
            barcode=get_field_value(data, 'barcode'),
            cost=data['standard_price'],
            price=data['list_price'],  # data['list_price'],
            taxRate=0.19,
            imageUrl="",
            description=get_field_value(data, 'description'),
            weight=data['weight'],
            uom=get_field_value(data, 'uom_name'),
            active=data['active'],
            additionalFields=additionalFields
        )
        return product


class OdooProductPackagingServiceBase:

    def __init__(self, key_index, *args, **kwargs):
        self.key_index = key_index
        self.mdb_product_packaging = OdooPackagingMongoDB()
        if key_index is not None:
            api_key = OdooAPIKey.from_json(key_index)
            self.api = OdooProductPackagingAPI(api_key, **kwargs)
            self.alias = self.api.get_alias()
            self.username = self.api.get_username()
            logger.info(f"Odoo username: {self.username} ({self.alias})")

    def __enter__(self):
        self.mdb_product_packaging.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mdb_product_packaging.close()

    def save_product_packaging(self, product_packaging_id):
        results = self.api.fetch_packaging_by_ids([product_packaging_id])
        if results is None or len(results) == 0:
            logger.error(f"Failed to fetch product packaging with id = {product_packaging_id}")
            return None
        item_data = results[0]
        fetchedAt = time_utils.now()
        create_date = convert_datetime_to_utc_format(item_data['create_date'])
        time.sleep(0.2)
        document = {
            '_id': product_packaging_id,
            'fetchedAt': fetchedAt,
            'createdAt': create_date,
            'data': item_data,
            'alias': self.api.get_alias()
        }
        return self.mdb_product_packaging.save_packaging(product_packaging_id, document)

    def to_standard_packaging(self, product_packaging_data) -> dict:
        pass


class OdooContactServiceBase:

    def __init__(self, key_index, *args, **kwargs):
        self.key_index = key_index
        self.mdb_contact = OdooContactMongoDB()
        if key_index is not None:
            api_key = OdooAPIKey.from_json(key_index)
            self.api = OdooContactAPI(api_key, **kwargs)
            self.alias = self.api.get_alias()
            self.username = self.api.get_username()
            logger.info(f"Odoo username: {self.username} ({self.alias})")

    def __enter__(self):
        self.mdb_contact.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mdb_contact.close()

    def save_contact(self, contact_id):
        results = self.api.fetch_contacts_by_ids([contact_id])
        if results is None or len(results) == 0:
            logger.error(f"Failed to fetch contact with id = {contact_id}")
            return None
        item_data = results[0]
        fetchedAt = time_utils.now()
        create_date = convert_datetime_to_utc_format(item_data['create_date'])
        time.sleep(0.2)

        document = {
            '_id': contact_id,
            'fetchedAt': fetchedAt,
            'createdAt': create_date,
            'data': item_data,
            'alias': self.api.get_alias()
        }
        return self.mdb_contact.save_contact(contact_id, document)

    def to_standard_address(self, contact) -> Address:
        c = contact['data']
        is_company = bool(c['is_company'])
        if is_company:
            name1 = c['name']
            name2 = ""
        else:
            name1 = c['name']
            name2 = c['parent_name'] if c['parent_name'] else ""

        if name1 == False:
            name1 = ""

        addr = Address(
            name1=name1,
            name2=name2,
            name3=c['street2'] if c['street2'] else "",
            street1=c['street'] if c['street'] else "",
            zipCode=c['zip'] if c['zip'] else "",
            city=c['city'] if c['city'] else "",
            province="",
            email=c['email'] if c['email'] else "",
            telephone=c['phone'] if c['phone'] else "",
            mobile=c['mobile'] if c['mobile'] else "",
            fax="",
            country=c['country_code'] if c['country_code'] else "",
        )
        return addr


# line = {
#     "order_number": odl['order_id'][1],  # 订单号
#     "product_name": odl['product_template_id'][1],
#     "product_id": odl['product_template_id'][0],
#     "internal_reference": __extract_internal_ref_from_product_name(odl['product_template_id'][1]),
#     "currency": odl['currency_id'][1],
#     "order_partner": odl['order_partner_id'][1],  # 客户
#     "salesman": odl['salesman_id'][1],  # 销售员
#     'state': odl['state'],
#     'uom': odl['product_uom'][1],  # 单位
#     'product_uom_qty': odl['product_uom_qty'],  # product_qty
#     'product_qty': odl['product_qty'],  # 数量
#     'price_unit': odl['price_unit'],  # 单价
#     'price_subtotal': odl['price_subtotal'],  # 小计
#     'price_tax': odl['price_tax'],  # 含税
#     'price_total': odl['price_total'],  # 总计
#     'qty_to_invoice': odl['qty_to_invoice'],
#     'qty_to_deliver': odl['qty_to_deliver'],
#     'product_type': odl['product_type'],
#     'create_date': odl['create_date'],
#     'is_delivery': odl['is_delivery'],
#     'discount': odl['discount'],
# }

class OrderLine(BaseModel):
    order_number: str
    product_name: str
    product_id: int
    internal_reference: str
    currency: str
    order_partner: str
    salesman: str
    state: str
    uom: str
    product_uom_qty: float
    product_qty: float
    price_unit: float
    price_subtotal: float
    price_tax: float
    price_total: float
    qty_to_invoice: float
    qty_to_deliver: float
    product_type: str
    create_date: str
    is_delivery: bool
    discount: float

class OdooOrderServiceBase:

    def __init__(self, key_index, *args, **kwargs):
        self.key_index = key_index
        self.mdb_order = OdooOrderlineMongoDB()
        if key_index is not None:
            api_key = OdooAPIKey.from_json(key_index)
            self.api = OdooOrderAPI(api_key, **kwargs)
            self.alias = self.api.get_alias()
            self.username = self.api.get_username()
            logger.info(f"Odoo username: {self.username} ({self.alias})")

    def save_all_orderlines(self):
        orderline_ids = self.api.fetch_orderline_ids()
        orderlines = self.api.fetch_orderline_by_ids(orderline_ids)
        fetchedAt = time_utils.now()
        list_ids_ = []
        list_docs = []
        for line in orderlines:
            id_ = line["id"]
            list_ids_.append(id_)
            create_date = convert_datetime_to_utc_format(line['create_date'])
            doc_ = {
                "_id": id_,
                "fetchedAt": fetchedAt,
                "createdAt": create_date,
                "data": line,
                "alias": self.api.get_alias()
            }
            list_docs.append(doc_)
        logger.info(f"Saving orderlines")
        return self.mdb_order.save_orderlines(list_ids_, list_docs)

    def __extract_internal_ref_from_product_name(self, product_name):
        # 正则表达式匹配中括号内的内容
        pattern = r'\[(.*?)\]'
        match = re.search(pattern, product_name)
        content = ""
        if match:
            content = match.group(1)
        else:
            print(f"No match found: {product_name}")
        return content

    def to_standard_orderline(self, orderline_data) -> OrderLine:
        odl = orderline_data
        if odl['product_template_id'] == False:
            raise ValueError(f"product_template_id is False")

        orderline = OrderLine(
            order_number= odl['order_id'][1],
            product_name=odl['product_template_id'][1],
            product_id=odl['product_template_id'][0],
            internal_reference=self.__extract_internal_ref_from_product_name(odl['product_template_id'][1]),
            currency=odl['currency_id'][1],
            order_partner=odl['order_partner_id'][1],
            salesman=odl['salesman_id'][1],
            state=odl['state'],
            uom=odl['product_uom'][1],
            product_uom_qty=odl['product_uom_qty'],
            product_qty=odl['product_qty'],
            price_unit=odl['price_unit'],
            price_subtotal=odl['price_subtotal'],
            price_tax=odl['price_tax'],
            price_total=odl['price_total'],
            qty_to_invoice=odl['qty_to_invoice'],
            qty_to_deliver=odl['qty_to_deliver'],
            product_type=odl['product_type'],
            create_date=odl['create_date'],
            is_delivery=odl['is_delivery'],
            discount=odl['discount'],
        )
        return orderline

    def __enter__(self):
        self.mdb_order.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mdb_order.close()
