from typing import List

import external.odoo.product as ext_product
import models.warehouse as mwh
from schemas.barcode import ProductFullInfo, ProductUpdate, Quant
from services.odoo import OdooProductService, OdooInventoryService

class OdooScannerService:

    def __init__(self, key_index, login=True, *args, **kwargs):
        self.svc_product = OdooProductService(key_index, login=login)
        self.mdb_product = self.svc_product.mdb_product
        self.svc_inventory = OdooInventoryService(key_index, login=False)
        self.mdb_quant = self.svc_inventory.mdb_quant
        self.mdb_putaway_rule = self.svc_inventory.mdb_putaway_rule
        self.mdb_location = self.svc_inventory.mdb_location
        self.api = self.svc_product.api

    def __enter__(self):
        self.svc_product.__enter__()
        self.svc_inventory.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.svc_product.__exit__(exc_type, exc_val, exc_tb)
        self.svc_inventory.__exit__(exc_type, exc_val, exc_tb)


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
            "qty_available": d.get("qty_available", 0),
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
        # query product from DB
        # filter_ = {"alias": self.api.get_alias(), "data.id": id}
        product_ = self.mdb_product.query_product_by_id(id)
        if not product_:
            return []

        quant_ids = product_['data']["stock_quant_ids"]

        data = self.svc_inventory.query_quants_by_quant_ids(quant_ids, offset=0, limit=1000)
        model_quants: List[mwh.Quant] = data['quants']
        quants = []
        for mq in model_quants:
            quant = {
                "id": mq.id,
                "product_id": mq.productId,
                "product_name": mq.productName,
                "product_uom": mq.productUom,
                "sku": mq.sku,
                "quantity": mq.quantity,
                "reserved_quantity": mq.reservedQuantity,
                "available_quantity": mq.availableQuantity,
                "location_name": mq.locationName,
                "location_id": mq.locationId,
                "location_code": mq.locationCode,
                "warehouse_id": mq.warehouseId,
                "warehouse_name": mq.warehouseName,
                "last_count_date": mq.lastCountDate,
            }
            quant = Quant(**quant)
            quants.append(quant)
        return quants