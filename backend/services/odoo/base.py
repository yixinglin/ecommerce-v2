import base64
import os
import time
from core.log import logger
from crud.odoo import (OdooQuantMongoDB,
                       OdooStorageLocationMongoDB,
                       OdooPutawayRuleMongoDB,
                       OdooProductTemplateMongoDB, OdooContactMongoDB, OdooProductMongoDB, OdooPackagingMongoDB)
from external.odoo import OdooAPIKey, OdooInventoryAPI, OdooProductAPI, OdooContactAPI
from external.odoo import DATETIME_PATTERN as ODOO_DATETIME_PATTERN
import utils.time as time_utils
from external.odoo.order import OdooOrderAPI
from external.odoo.product import OdooProductPackagingAPI
from models import Address
from models.orders import StandardProduct
from models.warehouse import Quant
import re

from utils import stringutils


def need_to_fetch(query_mothed, id, current_write_date: str):
    """
    Check if the record in DB needs to be fetched again.
    The record needs to be fetched if it is not found in DB or
    if the last write date is different from the current write date.
    :param query_mothed: A callback function of a query method of the DB
    :param id: The id of the record in Odoo
    :param current_write_date: The current write date of the record in Odoo
    :return:  True if the record needs to be fetched, False otherwise
    """
    item = query_mothed(id)
    if item is None:
        # Do not find the record in DB, need to fetch it
        return True
    else:
        last_write_date = item['data']['write_date']
        if last_write_date != current_write_date:
            # The record in DB is outdated, need to fetch it
            return True
        else:
            # The record in DB is up-to-date, no need to fetch it
            return False


def save_record(fetch_object_ids, fetch_write_date,
                query_object_by_id, object_name, save_object):
    """
    Save records from Odoo API to MongoDB if the record has changed since last fetch.

    :param fetch_object_ids: A callback function of a fetch method of the Odoo API
    :param fetch_write_date: A callback function of a fetch method of the Odoo API
    :param query_object_by_id: A callback function of a query method of the MongoDB
    :param object_name: The name of the object to be saved
    :param save_object: A callback function of a save method of the MongoDB
    """
    object_ids = fetch_object_ids()  # Fetch object ids from Odoo API
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


def convert_datetime_to_utc_format(odoo_datetime:str):
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
            logger.info(f"Using Odoo API Key: {api_key.alias}")
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

    def save_putaway_rule(self, putaway_rule_id):
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
            inventoryDiffQuantity=int(data['inventory_diff_quantity']),
            locationName=location_name,
            locationId=str(data['location_id'][0]),
            locationCode="",
            warehouseId=str(data['warehouse_id'][0]),
            warehouseName=data['warehouse_id'][1],
            lastCountDate= last_count_date,
        )
        return q

class OdooProductServiceBase:

    def __init__(self, key_index, *args, **kwargs):
        self.key_index = key_index
        self.mdb_product_templ = OdooProductTemplateMongoDB()
        self.mdb_product = OdooProductMongoDB()
        if key_index is not None:
            api_key = OdooAPIKey.from_json(key_index)
            logger.info(f"Using Odoo API Key: {api_key.alias}")
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
        mid = int(len(b64_image)/2)
        md5 = stringutils.text_to_md5(b64_image[:256] + b64_image[mid-256:mid+256] + b64_image[-256:])
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
        fetchedAt= product_data['fetchedAt']
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
            logger.info(f"Using Odoo API Key: {api_key.alias}")
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
            logger.info(f"Using Odoo API Key: {api_key.alias}")
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



class OdooOrderServiceBase:

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_index = key_index
        self.mdb_order = None
        if key_index is not None:
            api_key = OdooAPIKey.from_json(key_index)
            logger.info(f"Using Odoo API Key: {api_key.alias}")
            self.api = OdooOrderAPI(api_key, **kwargs)
            self.alias = self.api.get_alias()
            self.username = self.api.get_username()
            logger.info(f"Odoo username: {self.username} ({self.alias})")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

