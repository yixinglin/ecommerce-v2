import re
import xmlrpc
from typing import List

from pydantic import BaseModel

import utils.time as time_utils
from core.config2 import settings
from core.log import logger
from models import Address
from models.orders import StandardProduct
from schemas.vip import VipOrder, PimProduct, SpuProduct, SkuProduct
from utils.stringutils import split_seller_sku
from .base import (OdooProductServiceBase, OdooContactServiceBase, OdooProductPackagingServiceBase,
                   convert_datetime_to_utc_format, OrderLine, OdooServiceBase)
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
        filter_ = {
            "alias": self.api.get_alias(),
            "data.active": True,
            "data.default_code": code
        }
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

    def query_contact_by_vip_id(self, vip_id: int) -> dict:
        filter_ = {"alias": self.api.get_alias(), "data.x_studio_vip_id": vip_id}
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

    def create_sales_order(self, order: VipOrder):
        # TODO: 可以改成在线形式，而不是离线。
        order_line_data = []
        for line in order.orderLines:
            code = line.sellerSKU
            base, n_pack = split_seller_sku(code)
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

        if order.buyerId is not None:
            contact_by_vipid = self.svc_contact.query_contact_by_vip_id(order.buyerId)
        else:
            contact_by_vipid = None
        contact_by_name = self.svc_contact.query_contact_by_company_name(order.shipAddress.name1, email=order.shipAddress.email)

        contactName = ""
        if contact_by_vipid is not None:
            logger.info(f"Found contact by vip_id: {contact_by_vipid['name']}")
            contactId = contact_by_vipid['id']
            contactName = f"{contact_by_vipid['contact_address_inline']} <{contact_by_vipid['email']}>"
        elif contact_by_name is not None:
            logger.info(f"Found contact by name: {contact_by_name['name']}")
            contactId = contact_by_name['id']
            contactName = f"{contact_by_name['contact_address_inline']} <{contact_by_name['email']}>"
        else:
            raise RuntimeError(f"Company name {order.shipAddress.name1} <{order.shipAddress.email}> dose not match any contact in the Odoo Database.")

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

class OdooHsmsService(OdooServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

    def create_sales_order_vip(self, order: VipOrder):
        # TODO: 在线形式
        cli = self.api.client
        order_line_data = []
        for line in order.orderLines:
            code = line.sellerSKU
            base, n_pack = split_seller_sku(code)
            # 查找产品模板
            product_ids = cli.search(
                'product.product',
                [[['default_code', '=', base]]],
                {'limit': 1}
            )
            if not product_ids:
                logger.error(f"Product {code} not found")
                raise RuntimeError(f"Product [{code}] does not match any product in the Odoo Database.")
            product_id = product_ids[0]  # Product ID of Odoo Database (product.product)
            product_uom_qty = line.quantity * n_pack  # Convert to quantity in Odoo UOM
            price_unit = line.price / n_pack  # Convert to unit price in Odoo UOM
            order_line_data.append((0, 0, {
                'product_id': product_id,  # 产品ID（必填）
                'product_uom_qty': product_uom_qty,  # 产品数量
                'price_unit': price_unit,  # 单价
            }))

        if order.buyerId is not None:
            pass
        else:
            pass

        pass 




    def create_product_from_pim(self, pim_product: PimProduct):
        if pim_product.spu is None:
            raise RuntimeError(f"Data has no SPU")

        if pim_product.skuList is None or len(pim_product.skuList) == 0:
            raise RuntimeError(f"Data has no SKU")

        sku_product = pim_product.skuList[0]
        spu_product = pim_product.spu

        logger.info("Post Data: %s", pim_product)

        # --------- Step 1: Update to odoo_product
        result_product = self._create_product_form_pim(spu_product, sku_product)

        # ----------  Step 2: Update to supplierinfo
        # TODO: 供应商名字
        supplier_name = "Laboratorium Dr. Deppe GmbH"
        result_supplierinfo = self._create_supplier_info_from_pim(supplier_name, spu_product, sku_product)

        # --------------  Step 3 Update to packaging
        result_packaging_palette = self._create_packaging_from_pim("Palette", spu_product, sku_product)
        result_packaging_carton = self._create_packaging_from_pim("Karton", spu_product, sku_product)
        return {
            "product": result_product,
            "supplierinfo": result_supplierinfo,
            "packaging_palette": result_packaging_palette,
            "packaging_carton": result_packaging_carton,
        }

    def _create_product_form_pim(self, spu_product: SpuProduct, sku_product: SkuProduct):
        cli = self.api.client

        product_data = {
            'default_code': sku_product.skuCode,
            'name': sku_product.skuName,
            'list_price': sku_product.price,
            'standard_price': sku_product.cost,
            'type': 'product',
            'weight': sku_product.weight,
            'barcode': sku_product.packCode,
            'description_sale': spu_product.description,
        }

        product_vals = product_data

        default_code = product_vals.get('default_code')
        if not default_code:
            raise ValueError("default_code（SKU Code） is missing")

        existing_ids = cli.search(
            'product.template',
            [[['default_code', '=', default_code]]],
            {'limit': 1}
        )

        result = {}
        try:
            if existing_ids:
                pid = existing_ids[0]
                logger.info("Updating product information")
                cli.write('product.template', [[pid], product_vals])
                result = {"id": pid, "action": "updated"}
            else:
                logger.info("Creating product")
                pid = cli.create('product.template', [product_vals])
                result = {"id": pid, "action": "created"}
        except xmlrpc.client.Fault as e:
            logger.error(f"Failed to upload data to Odoo. {e}")
            raise RuntimeError(f"Failed to upload data to Odoo. {e}")

        return result

    def _create_supplier_info_from_pim(
            self,
            supplier_name: str,
            spu_product: SpuProduct,
            sku_product: SkuProduct
    ):
        cli = self.api.client
        default_code = sku_product.skuCode

        supplierinfo_data = {
            'product_code': sku_product.skuCodeOrigin,
            'min_qty': sku_product.cartonQuantity,
            'price': sku_product.cost,
            'delay': spu_product.leadTime,
        }

        supplierinfo_vals = supplierinfo_data

        # 查找产品模板
        product_ids = cli.search(
            'product.template',
            [[['default_code', '=', default_code]]],
            {'limit': 1}
        )

        if not product_ids:
            raise RuntimeError(f"Failed to find product with default_code '{default_code}'")
        product_id = product_ids[0]

        # 查找供应商
        supplier_ids = cli.search(
            'res.partner',
            [[['name', '=', supplier_name]]],
            {'limit': 1}
        )
        if not supplier_ids:
            raise ValueError(f"Failed to find supplier with name '{supplier_name}'")
        supplier_id = supplier_ids[0]

        # FIX: supplierinfo 查找必须加入 product_code，否则会误更新其他 SKU
        existing_ids = cli.search(
            'product.supplierinfo',
            [[
                ['partner_id', '=', supplier_id],
                ['product_tmpl_id', '=', product_id],
                ['product_code', '=', sku_product.skuCodeOrigin]  # BUGFIX
            ]],
            {'limit': 1}
        )

        # 填充必要字段
        supplierinfo_vals['partner_id'] = supplier_id
        supplierinfo_vals['product_tmpl_id'] = product_id

        try:
            if existing_ids:
                sid = existing_ids[0]
                logger.info(f"Updating supplierinfo for {supplier_name}")
                cli.write('product.supplierinfo', [[sid], supplierinfo_vals])
                logger.info(f"Updated supplierinfo (ID: {sid})，产品: {default_code}, 供应商: {supplier_name}")
                result = {'id': sid, 'action': 'updated'}
            else:
                logger.info(f"Creating supplierinfo for {supplier_name}")
                sid = cli.create('product.supplierinfo', [supplierinfo_vals])
                logger.info(f"Created supplierinfo (ID: {sid})，产品: {default_code}, 供应商: {supplier_name}")
                result = {'id': sid, 'action': 'created'}
        except xmlrpc.client.Fault as e:
            logger.error(f"Failed to update supplierinfo. {e}")
            raise RuntimeError(f"Failed to update supplierinfo. {e}")

        return result

    def _create_packaging_from_pim(
            self,
            packaging_name: str,
            spu_product: SpuProduct,
            sku_product: SkuProduct
    ):
        cli = self.api.client
        default_code = sku_product.skuCode
        if packaging_name == "Karton":
            qty = sku_product.cartonQuantity
            barcode = sku_product.cartonCode
            sequence = 1
        else:  # Palette
            qty = sku_product.palletQuantity
            barcode = sku_product.palletCode
            sequence = 2

        packaging_data = {
            'qty': qty,
            'barcode': barcode,
            'sequence': sequence,
        }

        packaging_vals = packaging_data

        # 查找变体产品
        product_ids = cli.search(
            'product.product',
            [[['default_code', '=', default_code]]],
            {'limit': 1}
        )

        if not product_ids:
            raise RuntimeError(f"Failed to find product [{default_code}]")
        product_id = product_ids[0]

        existing_ids = cli.search(
            'product.packaging',
            [[
                ['product_id', '=', product_id],
                ['name', '=', packaging_name],
            ]],
            {'limit': 1}
        )

        packaging_vals['name'] = packaging_name
        packaging_vals['product_id'] = product_id

        try:
            if existing_ids:
                pid = existing_ids[0]
                cli.write('product.packaging', [[pid], packaging_vals])
                logger.info(f"Updated packaging (ID: {pid})，Product: {default_code}, Packaging: {packaging_name}")
                result = {'id': pid, 'action': 'updated'}
            else:
                pid = cli.create('product.packaging', [packaging_vals])
                logger.info(f"Created packaging (ID: {pid})，Product: {default_code}, Packaging: {packaging_name}")
                result = {'id': pid, 'action': 'created'}
        except xmlrpc.client.Fault as e:
            logger.error(f"Failed to update packaging. {e}")
            raise RuntimeError(f"Failed to update packaging. {e}")

        return result





