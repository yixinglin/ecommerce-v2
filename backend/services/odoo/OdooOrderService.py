import re
from typing import List

from pydantic import BaseModel

import utils.time as time_utils
from core.config2 import settings
from core.log import logger
from models import Address
from models.orders import StandardProduct
from schemas.vip import VipOrder
from .base import (OdooProductServiceBase, OdooContactServiceBase, OdooProductPackagingServiceBase,
                   convert_datetime_to_utc_format, OrderLine)
from .base import save_record, OdooOrderServiceBase
import utils.address as addr_utils

odoo_access_key_index = settings.api_keys.odoo_access_key_index

class OdooProductService(OdooProductServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

    def save_all_product_templates(self):
        fetch_object_ids = self.api.fetch_product_template_ids
        fetch_write_date = self.api.fetch_product_template_write_date
        query_object_by_id = self.mdb_product_templ.query_product_template_by_id
        save_object = self.save_product_template
        object_name = 'product.template'
        save_record(fetch_object_ids, fetch_write_date,
                    query_object_by_id, object_name, save_object,
                    include_inactive=True)

    def save_all_products(self):
        fetch_object_ids = self.api.fetch_product_ids
        fetch_write_date = self.api.fetch_product_write_date
        query_object_by_id = self.mdb_product.query_product_by_id
        save_object = self.save_product
        object_name = 'product.product'
        save_record(fetch_object_ids, fetch_write_date,
                    query_object_by_id, object_name, save_object,
                    include_inactive=True)

    def query_all_product_templates(self, offset, limit):
        # Query all products from DB
        filter_ = {"alias": self.api.get_alias(), "data.active": True,  "data.type": "product"}
        data = self.mdb_product_templ.query_product_templates(offset=offset, limit=limit, filter=filter_)
        products = []
        for product in data:
            # To standard product object
            p = self.to_standard_product(product)
            products.append(p)
        ans = dict(
            alias=self.api.get_alias(),
            size=len(products),
            products=products,
        )
        return ans

    def query_product_templates_by_ids(self, ids: List[int]):
        # Query products by ids from DB
        filter_ = {"alias": self.api.get_alias(), "data.id": {"$in": ids}}
        data = self.mdb_product_templ.query_product_templates(filter=filter_)
        products = []
        for product in data:
            # To standard product object
            p = self.to_standard_product(product)
            products.append(p)
        return products

    def query_product_by_code(self, code) -> StandardProduct:
        filter_ = {"alias": self.api.get_alias(), "data.default_code": code}
        data = self.mdb_product.query_products(filter=filter_)
        if len(data) == 0:
            return None
        product = data[0]
        return self.to_standard_product(product)

    def query_product_by_id(self, id):
        filter_ = {"alias": self.api.get_alias(), "data.id": id}
        data = self.mdb_product.query_products(filter=filter_)
        if len(data) == 0:
            return None
        product = data[0]
        return self.to_standard_product(product)

    def query_all_products(self, offset, limit):
        # Query all products from DB
        filter_ = {"alias": self.api.get_alias(), "data.active": True, "data.type": "product"}
        data = self.mdb_product.query_products(offset=offset, limit=limit, filter=filter_)
        products = []
        for product in data:
            # To standard product object
            p = self.to_standard_product(product)
            products.append(p)
        ans = dict(
            alias=self.api.get_alias(),
            size=len(products),
            products=products,
        )
        return ans

class OdooProductPackagingService(OdooProductPackagingServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

    def save_all_product_packaging(self):
        fetch_object_ids = self.api.fetch_packaging_ids
        fetch_write_date = self.api.fetch_packaging_write_date
        query_object_by_id = self.mdb_product_packaging.query_packaging_by_id
        save_object = self.save_product_packaging
        object_name = 'product.packaging'
        save_record(fetch_object_ids, fetch_write_date,
                    query_object_by_id, object_name, save_object)

    def query_all_product_packaging(self, offset, limit):
        # Query all product packaging from DB
        filter_ = {"alias": self.api.get_alias()}
        data = self.mdb_product_packaging.query_packagings(offset=offset, limit=limit, filter=filter_)
        packagings = []
        for packaging in data:
            # To standard product packaging object
            # p = self.to_standard_product_packaging(packaging)
            p = packaging
            packagings.append(p)
        ans = dict(
            alias=self.api.get_alias(),
            size=len(packagings),
            packagings=packagings,
        )
        return ans

    def query_packaging_by_id(self, id):
        filter_ = {"alias": self.api.get_alias(), "data.id": id}
        data = self.mdb_product_packaging.query_packagings(filter=filter_)
        if len(data) == 0:
            return None
        packaging = data[0]
        return packaging.get('data', "")


class OdooContactService(OdooContactServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

    def save_all_contacts(self):
        fetch_object_ids = self.api.fetch_contact_ids
        fetch_write_date = self.api.fetch_contact_write_date
        query_object_by_id = self.mdb_contact.query_contact_by_id
        save_object = self.save_contact
        object_name = 'res.partner'
        save_record(fetch_object_ids, fetch_write_date,
                    query_object_by_id, object_name, save_object,
                    include_inactive=True)

    def query_all_contacts(self, offset, limit):
        # Query all contacts from DB
        filter_ = {"alias": self.api.get_alias()}
        data = self.mdb_contact.query_contacts(offset=offset, limit=limit, filter=filter_)
        contacts = []
        for contact in data:
            # To standard contact object
            c = contact.get('data', "")
            contacts.append(dict(
                fetchedAt=contact.get('fetchedAt', ""),
                contact=c,))
        ans = dict(
            alias=self.api.get_alias(),
            size=len(contacts),
            contacts=contacts,
        )
        return ans


    def query_all_contact_shipping_addresses(self, offset, limit):
        # Query all shipping addresses of a contact from DB
        filter_ = {"alias": self.api.get_alias(), "data.active": True}
        data = self.mdb_contact.query_contacts(offset=offset, limit=limit, filter=filter_)
        addresses: Address = []
        for contact in data:
            try:
                addr = self.to_standard_address(contact)
                addresses.append(addr)
            except Exception as e:
                logger.error(f"Failed to convert contact to address: {e}")
                logger.error(f"Contact: {contact['data']['name']}, {contact['data']['id']}")
        ans = dict(
            alias=self.api.get_alias(),
            size=len(addresses),
            addresses=addresses,
        )
        return ans

    def query_contact_by_company_name(self, company_name, email=None):
        company_regex = re.compile(f"{company_name.strip()}", re.IGNORECASE)

        filter_ = {
            "alias": self.api.get_alias(),
            "data.name": company_regex,
            "data.active": True
        }

        if email:
            # 提取 email 域名部分（含 @）
            email_domain = email[email.find("@"):].strip()
            email_regex = re.compile(f"{re.escape(email_domain)}$", re.IGNORECASE)
            filter_["data.email"] = email_regex

        data = self.mdb_contact.query_contacts(filter=filter_)
        if not data:
            return None

        contact = data[0]
        return contact.get('data', "")

    def query_contact_by_id(self, id):
        filter_ = {"alias": self.api.get_alias(), "data.id": id}
        data = self.mdb_contact.query_contacts(filter=filter_)
        if len(data) == 0:
            return None
        contact = data[0]
        return contact.get('data', "")


class OdooOrderService(OdooOrderServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)
        self.svc_product = OdooProductService(key_index, *args, **kwargs)
        self.svc_contact = OdooContactService(key_index, *args, **kwargs)

    def __enter__(self):
        super().__enter__()
        self.svc_product.__enter__()
        self.svc_contact.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self.svc_product.__exit__(exc_type, exc_val, exc_tb)
        self.svc_contact.__exit__(exc_type, exc_val, exc_tb)


    def query_orderline_by_id(self, id) -> OrderLine:
        filter_ = {"alias": self.api.get_alias(), "data.id": id}
        data = self.mdb_order.query_orderlines(filter=filter_)
        if len(data) == 0:
            return None
        orderline = data[0]
        return self.to_standard_orderline(orderline.get('data', ""))

    def query_orderlines_by_order_id(self, order_id) -> List[OrderLine]:
        filter_ = {"alias": self.api.get_alias(), "data.order_id": order_id}
        data = self.mdb_order.query_orderlines(filter=filter_)
        if len(data) == 0:
            return None
        orderlines = []
        for li in data:
            try:
                line = self.to_standard_orderline(li.get('data', ""))
                orderlines.append(line)
            except Exception as e:
                logger.error(f"Failed to convert orderline to standard: {e}")
                logger.error(f"Orderline: {li['data']['id']}")
        return orderlines

    def query_orderlines_by_salesman_id(self, salesman_ids: List[int]) -> List[OrderLine]:
        filter_ = {"alias": self.api.get_alias()}
        if salesman_ids is not None:
            filter_["data.salesman_id"] = {"$in": salesman_ids}

        data = self.mdb_order.query_orderlines(filter=filter_)
        if len(data) == 0:
            return None
        orderlines = []
        for li in data:
            try:
                line = self.to_standard_orderline(li.get('data', ""))
                orderlines.append(line)
            except Exception as e:
                logger.error(f"Failed to convert orderline [id={li['data']['id']}] to standard: {e}")
        return orderlines

    def split_seller_sku(self, seller_sku):
        pattern = r"^(.*?)(PK\d+)$"
        match = re.match(pattern, seller_sku)
        if match:
            base = match.group(1)
            n_pack = match.group(2)
            n_pack = int(n_pack.replace("PK", ""))
        else:
            base = seller_sku
            n_pack = 1
        return base, n_pack

    def create_sales_order(self, order: VipOrder):
        order_line_data = []
        for line in order.orderLines:
            code = line.sellerSKU
            base, n_pack = self.split_seller_sku(code)
            product = self.svc_product.query_product_by_code(base)
            if not product:
                logger.error(f"Product {code} not found")
                raise RuntimeError(f"Product [{code}] does not match any product in the Odoo Database.")
            product_id = int(product.id)  # Product ID of Odoo Database (product.product)
            product_uom_qty = line.quantity * n_pack  # Convert to quantity in Odoo UOM
            price_unit = line.price / n_pack  # Convert to unit price in Odoo UOM
            order_line_data.append((0, 0, {
                'product_id': product_id,  # 产品ID（必填）
                'product_uom_qty': product_uom_qty,  # 产品数量
                'price_unit': price_unit,  # 单价
            }))

        contact = self.svc_contact.query_contact_by_company_name(order.shipAddress.name1, email=order.shipAddress.email)
        testContact = self.svc_contact.query_contact_by_company_name("Test-Kunde GmbH", email=None)
        contactName = ""
        if contact is not None:
            logger.info(f"Found contact: {contact['name']}")
            contactId = contact['id']
            contactName = contact['name']
        elif testContact is not None:
            logger.info(f"Found test contact: {testContact['name']}")
            contactId = testContact['id']
            contactName = testContact['name']
        else:
            raise RuntimeError(f"Company name {order.shipAddress.name1} dose not match any contact in the Odoo Database.")

        quot_data = {
            'partner_id': contactId,  # 客户ID（必填）
            'order_line': order_line_data,  # 订单行信息
            'client_order_ref': order.orderId,  # 客户订单号（必填）
        }

        logger.info(f"Creating order: {quot_data}")
        if not settings.app.debug or odoo_access_key_index == 0:
            self.api.create_sales_order(quot_data)
            logger.info(f"Order created")
        else:
            logger.info(f"Debug mode, not creating order")

        ans = dict(
            contact_name=contactName,
            quot_data=quot_data,
        )

        return ans

    def query_delivery_order_by_order_number(self, order_number):
        self.api.login()
        orders = self.api.fetch_delivery_order(order_number)
        if not orders:
            logger.error(f"Delivery order {order_number} not found")
            raise RuntimeError(f"Delivery order {order_number} not found")
        order = orders[0]
        partner_id = order['partner_id'][0]
        partner_name = order['partner_id'][1]
        contact = self.svc_contact.query_contact_by_id(partner_id)
        if contact is not None:
            logger.info(f"Found contact: {contact['complete_name']}")
            # name1 = contact['name']
            address = self.convert_odoo_address_to_standard(contact)
            address = address.dict()

        origin = order['origin']
        result = {}
        result['references'] = [order_number]
        # if origin:
        #     result['references'].append(origin)
        result['create_date'] = order['create_date']
        result['consignee'] = address
        result['parcels'] = [{"weight": 1}]
        return result

    def convert_odoo_address_to_standard(self, odoo_address) -> Address:
        false_to_str = lambda x: x if x else ""
        name = false_to_str(odoo_address.get('complete_name', ""))  # complete_name
        street = false_to_str(odoo_address.get('street', ""))  # street
        street2 = false_to_str(odoo_address.get('street2', ""))  # street2
        zip_ = false_to_str(odoo_address.get('zip', ""))  # zip
        city = false_to_str(odoo_address.get('city', ""))  # city
        state = ""  # state
        country_code = odoo_address.get('country_code', "")
        email = false_to_str(odoo_address.get('email', ""))  # email
        phone = false_to_str(odoo_address.get('phone', ""))  # phone
        mobile = false_to_str(odoo_address.get('mobile', ""))  # mobile
        is_company = odoo_address.get('is_company', False)  # is_company
        lang = false_to_str(odoo_address.get('lang', ""))  # lang

        if country_code.lower() == "de":
            zip_ = zip_.upper().replace("DE-", "")

        country_code_white_list = ["DE"]
        if not country_code or country_code.upper() not in country_code_white_list:
            logger.error(f"Failed to identify German street: {street}, {street2}. Customer: {name}")
            raise RuntimeError(f"Do not support address from this country: {country_code}. Customer: {name}")

        if street == "" and street2 == "":
            logger.error(f"Address is empty. Customer: {name}")
            raise RuntimeError(f"Address is empty. Customer: {name}")

        split_1 = addr_utils.identify_german_street(street)
        split_2 = addr_utils.identify_german_street(street2)
        if split_1 is not None:
            pass
        elif split_2 is not None:
            street, street2 = street2, street
        else:
            logger.error(f"Failed to identify German street: {street}, {street2}. Customer: {name}")
            raise RuntimeError(f"Failed to identify German street: {street}, {street2}. Customer: {name}")

        # Note: name(company), street(street), street2(c/o)
        addr = {
            "name1": name,
            "name2": street2,
            "name3": "",
            "street1": street,
            "zipCode": zip_,
            "city": city,
            "province": "",
            "country": country_code.upper(),
            "email": email,
            "telephone": phone,
            "mobile": mobile,
        }

        return Address(**addr)







