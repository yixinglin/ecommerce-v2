from typing import List

from schemas.barcode import ProductFullInfo
from services.odoo.base import OdooProductServiceBase


class OdooScannerService(OdooProductServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

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
                product.image_url = self.save_product_image(b64_image)
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
            product.image_url = self.save_product_image(b64_image)
        else:
            product.image_url = ""
        return product
