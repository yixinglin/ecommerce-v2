from typing import List
import utils.time as utils_time
import external.odoo.product as ext_product
import models.warehouse as mwh
from core.config import settings
import time
from core.log import logger
from schemas.barcode import ProductFullInfo, ProductUpdate, Quant, ProductPackaging, ProductPackagingUpdate
from services.odoo import OdooProductService, OdooInventoryService
from services.odoo.OdooOrderService import OdooProductPackagingService


class OdooScannerService:

    def __init__(self, key_index, login=True, *args, **kwargs):
        self.svc_product = OdooProductService(key_index, login=login)
        self.mdb_product = self.svc_product.mdb_product
        self.svc_inventory = OdooInventoryService(key_index, login=False)
        self.mdb_quant = self.svc_inventory.mdb_quant
        self.mdb_putaway_rule = self.svc_inventory.mdb_putaway_rule
        self.mdb_location = self.svc_inventory.mdb_location
        self.svc_packaging = OdooProductPackagingService(key_index, login=False)
        self.mdb_packaging = self.svc_packaging.mdb_product_packaging
        self.api = self.svc_product.api

    def __enter__(self):
        self.svc_product.__enter__()
        self.svc_inventory.__enter__()
        self.svc_packaging.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.svc_product.__exit__(exc_type, exc_val, exc_tb)
        self.svc_inventory.__exit__(exc_type, exc_val, exc_tb)
        self.svc_packaging.__exit__(exc_type, exc_val, exc_tb)


    def __to_barcode_product_full_info(self, product_odoo) -> ProductFullInfo:
        d = product_odoo
        get_values = lambda k: "" if d.get(k, "") == False else d.get(k, "")
        p = {
            "id": d.get("id", ""),
            "sku": get_values("default_code"),
            "name": d.get("name", ""),
            "barcode": get_values("barcode"),
            "image_url": "",
            "description": get_values("description"),
            "weight": d.get("weight", 0.0),
            "qty_available": int(d.get("qty_available", 0)),
            "uom": d.get("uom_name", ""),
            "active": d.get("active", False),
        }
        return ProductFullInfo(**p)

    def query_products_by_keyword(self, keyword) -> List[ProductFullInfo]:
        filter_ = {"alias": self.api.get_alias(),
                   "$or": [
                       {"data.default_code":  {"$regex": keyword, "$options": "i"}},
                       {"data.barcode":  {"$regex": keyword, "$options": "i"}},
                       {"data.name":  {"$regex": keyword, "$options": "i"}},
                       {"data.description":  {"$regex": keyword, "$options": "i"}},
                   ]
                }
        products_data = self.mdb_product.query_products(filter=filter_)
        products = []
        for pdata in products_data:
            product = pdata.get('data', "")
            b64_image = product.get('image_256', "")
            product = self.__to_barcode_product_full_info(product)
            if b64_image != False and b64_image != "":
                product.image_url = self.svc_product.save_product_image(b64_image)
            else:
                product.image_url = ""
            products.append(product)
        products.sort(key=lambda x: x.sku)
        products = products[:50]
        return products

    def query_product_by_id(self, id) -> ProductFullInfo:
        data = self.mdb_product.query_product_by_id(id)
        if not data:
            return None
        product = data['data']
        b64_image = product.get('image_1920', "")
        product = self.__to_barcode_product_full_info(product)
        if b64_image != False and b64_image != "":
            product.image_url = self.svc_product.save_product_image(b64_image)
        else:
            product.image_url = ""
        return product

    def update_product_by_id(self, id, data: ProductUpdate):
        values_to_update = ext_product.ProductUpdate(
            id=id,
            barcode=data.barcode,
            weight=data.weight,
            image_1920=data.b64_image,
        )
        # update product in odoo
        self.api.update_product_by_id(id, values_to_update)
        # save product in database
        self.svc_product.save_product(id)
        # query product from database
        return self.query_product_by_id(id)

    def query_quants_by_product_id(self, id) -> List[Quant]:
        product_data = [self.mdb_product.query_product_by_id(id)]
        if not product_data:
            return []
        product_data = product_data[0]['data']
        quant_ids = product_data['stock_quant_ids']

        current_time = utils_time.now()
        data = self.svc_inventory.query_quants_by_quant_ids(quant_ids, offset=0, limit=1000)
        model_quants: List[mwh.Quant] = data['quants']
        quants = []
        for mq in model_quants:
            last_count_days = 0
            if mq.lastCountDate != None and mq.lastCountDate != "":
                last_count_days = utils_time.diff_datetime(current_time, mq.lastCountDate)
            last_count_days = int(last_count_days / (24 * 60 * 60))
            quant = {
                "id": mq.id,
                "product_id": mq.productId,
                "product_name": mq.productName,
                "product_uom": mq.productUom,
                "sku": mq.sku,
                "quantity": mq.quantity,
                "reserved_quantity": mq.reservedQuantity,
                "available_quantity": mq.availableQuantity,
                "inventory_quantity": mq.inventoryQuantity,
                "inventory_diff_quantity": mq.inventoryDiffQuantity,
                "location_name": mq.locationName,
                "location_id": mq.locationId,
                "location_code": mq.locationCode,
                "warehouse_id": mq.warehouseId,
                "warehouse_name": mq.warehouseName,
                "last_count_days": last_count_days,
            }
            quant = Quant(**quant)
            quants.append(quant)
        quants.sort(key=lambda x: x.location_code)
        return quants

    def request_quant_by_id(self, quant_id, inv_quantity):
        """ 发起库存调整请求  """
        api = self.svc_inventory.api.login()
        if True:
            success = api.request_quant_by_id(quant_id, inv_quantity)
        else:
            logger.info(f"DEBUG MODE: request_quant_by_id({quant_id}, {inv_quantity})")
            success = True
        if success:
            self.svc_inventory.save_quant(quant_id)
        return success

    def quant_relocation_by_id(self, quant_id, location_id):
        api = self.svc_inventory.api.login()
        # quant_data = self.mdb_quant.query_quant_by_id(quant_id)
        # product_id = quant_data['data']['product_id'][0]
        quant_data = api.fetch_quant_by_ids([quant_id])
        if not quant_data:
            return False
        product_id = quant_data[0]['product_id'][0]

        if True:
            success = api.quant_relocation_by_id(quant_id, location_id)
        else:
            logger.info(f"DEBUG MODE: request_quant_relocation({quant_id}, {location_id})")
            success = True

        if success:
            self.save_product_and_quants(product_id)
        return success

    def save_product_and_quants(self, product_id):
        self.svc_product.save_product(product_id)
        product_ = self.mdb_product.query_product_by_id(product_id)
        quant_ids = product_['data']['stock_quant_ids']
        for qid in quant_ids:
            self.svc_inventory.save_quant(qid)


    def query_location_by_barcode(self, barcode):
        filter_ = {"alias": self.api.get_alias(),
                   "data.barcode": barcode}
        location_data = self.mdb_location.query_storage_locations(filter=filter_, offset=0, limit=10)
        if not location_data:
            return None
        location = location_data[0]
        return location

    def __to_product_packaging(self, packaging_odoo) -> ProductPackaging:
        d = packaging_odoo
        get_values = lambda k: "" if d.get(k, "") == False else d.get(k, "")
        p = {
            "id": d.get("id", ""),
            "product_id": d.get("product_id")[0],
            "product_name": d.get("product_id")[1],
            "name": get_values("name"),
            "qty": d.get("qty", 0),
            "uom": d.get("product_uom_id", "")[1],
            "barcode": get_values("barcode"),
        }
        return ProductPackaging(**p)

    def query_packaging_by_product_ids(self, product_id) -> List[ProductPackaging]:
        # api = self.svc_packaging.api.login()
        product_data = self.mdb_product.query_product_by_id(product_id)
        packaging_ids = product_data['data']['packaging_ids']

        filter_ = {"alias": self.api.get_alias(),
                   "data.id": {"$in": packaging_ids}}
        packaging_data = self.mdb_packaging.query_packagings(filter=filter_)
        if not packaging_data:
            return []
        packagings = []
        for pd in packaging_data:
            packaging = pd['data']
            packaging = self.__to_product_packaging(packaging)
            packagings.append(packaging)
        return packagings

    def update_packaging_by_id(self, packaging_id, data: ProductPackagingUpdate) -> ProductPackaging:
        values_to_update = ext_product.PackagingUpdate(
            id=packaging_id,
            name=data.name,
            barcode=data.barcode,
            qty=data.qty,
        )
        # update packaging in odoo
        api = self.svc_packaging.api.login()
        if True:
            api.update_packaging_by_id(packaging_id, values_to_update)
        else:
            logger.info(f"DEBUG MODE: update_packaging_by_id({packaging_id}, {data})")
        # save packaging in database
        self.svc_packaging.save_product_packaging(packaging_id)
        # query packaging from database
        data = self.svc_packaging.query_packaging_by_id(packaging_id)
        return self.__to_product_packaging(data)
