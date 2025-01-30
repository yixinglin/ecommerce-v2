from typing import Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import settings
from core.log import logger
from schemas.barcode import ProductFullInfo, ProductBasicInfo
from services.odoo import OdooProductService
from services.odoo.OdooScannerServier import OdooScannerService

barcode = APIRouter(prefix="/product", )


@barcode.get("/kw/{keyword}", response_model=list[ProductBasicInfo])
def get_product_by_keyword(keyword):
    with OdooScannerService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        products = svc.query_products_by_keyword(keyword)
    return products

@barcode.get("/pid/{id}", response_model=ProductFullInfo)
def get_product_by_id(id):
    with OdooScannerService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        product = svc.query_product_by_id(int(id))
    if not product:
        logger.error(f"Product with id {id} not found")
        raise HTTPException(status_code=404, detail=f"Product with id {id} not found")
    return product

def update_product_by_id(product_id, data):
    pass

@barcode.put("/pid/{product_id}/barcode/{barcode}")
def update_product_barcode(product_id, barcode):
    with OdooScannerService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        product = svc.query_product_by_id(int(product_id))
        if not product:
            logger.error(f"Product with id {product_id} not found")
            raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
        product.barcode = barcode
    print(product)
    return product

@barcode.put("/pid/{product_id}/weight/{weight}")
def update_product_weight(product_id, weight):
    with OdooScannerService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        product = svc.query_product_by_id(int(product_id))
        if not product:
            logger.error(f"Product with id {product_id} not found")
            raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
        product.weight = weight
    return product




def get_inventories_by_product_id(product_id):
    pass

def update_inventory_by_id(inventory_id, data):
    pass

def delete_inventory_by_id(inventory_id):
    pass