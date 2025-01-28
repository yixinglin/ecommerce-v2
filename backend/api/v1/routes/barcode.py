from fastapi import APIRouter
from pydantic import BaseModel

from core.config import settings
from services.odoo import OdooProductService


barcode = APIRouter(prefix="/product", )


class ProductBasicInfo(BaseModel):
    id: int
    sku: str
    name: str
    barcode: str
    image_url: str
    description: str
    weight: float
    uom: str
    active: bool

class Inventory(BaseModel):
    id: int
    product_id: int
    loc_code: str
    quantity: float
    warehouse_id: int
    warehouse_name: str


@barcode.get("/kw/{keyword}", response_model=list[ProductBasicInfo])
def get_product_by_keyword(keyword):
    with OdooProductService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        products = svc.query_products_by_keyword(keyword)

    product_list = []
    for product in products:
        info = {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "barcode": product.barcode,
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Approve_icon.svg",
            "description": product.description,
            "weight": product.weight,
            "uom": product.uom,
            "active": product.active
        }
        product_list.append(ProductBasicInfo(**info))
    return product_list

def get_product_by_id(product_id):
    pass

def update_product_by_id(product_id, data):
    pass


def get_inventories_by_product_id(product_id):
    pass

def update_inventory_by_id(inventory_id, data):
    pass

def delete_inventory_by_id(inventory_id):
    pass