import base64
from typing import Union, List, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File


from core.config2 import settings
from core.log import logger
from schemas.barcode import ProductFullInfo, ProductBasicInfo, ProductUpdate, Quant, ProductPackaging, \
    ProductPackagingUpdate, PutawayRule, PutawayRuleUpdate
from services.odoo.OdooScannerServier import OdooScannerService

barcode = APIRouter(prefix="/product", )

odoo_access_key_index = settings.api_keys.odoo_access_key_index 

@barcode.get("/kw/{keyword}", response_model=list[ProductBasicInfo])
def get_product_by_keyword(keyword: str, offset: int = 0, limit: int = 50):
    with OdooScannerService(key_index=odoo_access_key_index, login=False) as svc:
        products = svc.query_products_by_keyword(keyword, offset=offset, limit=limit)
    return products


@barcode.get("/pid/{id}", response_model=ProductFullInfo)
def get_product_by_id(id: int, up_to_date: bool = False):
    with OdooScannerService(key_index=odoo_access_key_index, login=False) as svc:
        product = svc.query_product_by_id(id, update_db=up_to_date)
    if not product:
        logger.error(f"Product with id {id} not found")
        raise HTTPException(status_code=404, detail=f"Product with id {id} not found")
    return product


@barcode.put("/pid/{product_id}/barcode/{barcode}")
def update_product_barcode(product_id: int, barcode: str):
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        data = ProductUpdate(
            barcode=barcode.strip()
        )
        product = svc.update_product_by_id(product_id, data)
        if not product:
            logger.error(f"Product with id {product_id} not found")
            raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
    return product


@barcode.put("/pid/{product_id}/weight/{weight}")
def update_product_weight(product_id: int, weight: float):
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        data = ProductUpdate(
            weight=weight
        )
        product = svc.update_product_by_id(product_id, data)
        if not product:
            logger.error(f"Product with id {product_id} not found")
            raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
    return product


@barcode.put("/pid/{product_id}/image")
def update_product_image(product_id: int, image: UploadFile = File(...)):
    b64_image = base64.b64encode(image.file.read()).decode('utf-8')
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        data = ProductUpdate(
            b64_image=b64_image
        )
        product = svc.update_product_by_id(product_id, data)
        if not product:
            logger.error(f"Product with id {product_id} not found")
            raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
    return product


@barcode.get("/pid/{product_id}/quants", response_model=list[Quant])
def get_quants_by_product_id(product_id: int):
    with OdooScannerService(key_index=odoo_access_key_index, login=False) as svc:
        quants = svc.query_quants_by_product_id(product_id)
    return quants


@barcode.put("/qid/{quant_id}/qty/{quantity}", response_model=bool)
def request_quant_by_id(quant_id: int, quantity: int):
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        success = svc.request_quant_by_id(quant_id, quantity)
    return success


@barcode.put("/qid/{quant_id}/relocation/to_location/{barcode}", response_model=bool)
def quant_relocation_by_id(quant_id: int, barcode: str):
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        loca_data = svc.query_location_by_barcode(barcode)
        if not loca_data:
            logger.error(f"Location with barcode {barcode} not found")
            raise HTTPException(status_code=404, detail=f"Location with barcode {barcode} not found")
        location_id = loca_data['data']['id']
        success = svc.quant_relocation_by_id(quant_id, location_id)
    return success


def update_inventory_by_id(inventory_id, data):
    pass


def delete_inventory_by_id(inventory_id):
    pass


@barcode.get("/pid/{product_id}/packaging", response_model=list[ProductPackaging])
def get_packaging_by_product_id(product_id: int):
    with OdooScannerService(key_index=odoo_access_key_index, login=False) as svc:
        packaging = svc.query_packaging_by_product_ids(product_id)
    return packaging


@barcode.put("/pkid/{packaging_id}/barcode/{barcode}", response_model=ProductPackaging)
def update_packaging_barcode_by_id(packaging_id: int, barcode: str):
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        data = ProductPackagingUpdate(
            barcode=barcode.strip()
        )
        packaging = svc.update_packaging_by_id(packaging_id, data)
        if not packaging:
            logger.error(f"Packaging with id {packaging_id} not found")
            raise HTTPException(status_code=404, detail=f"Packaging with id {packaging_id} not found")
    return packaging


@barcode.put("/pkid/{packaging_id}/quantity/{quantity}", response_model=ProductPackaging)
def update_packaging_quantity_by_id(packaging_id: int, quantity: int):
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        data = ProductPackagingUpdate(
            qty=quantity
        )
        packaging = svc.update_packaging_by_id(packaging_id, data)
        if not packaging:
            logger.error(f"Packaging with id {packaging_id} not found")
            raise HTTPException(status_code=404, detail=f"Packaging with id {packaging_id} not found")
    return packaging


@barcode.get("/pid/{product_id}/putaway_rules", response_model=list[PutawayRule])
def query_putaway_rules_by_product_id(product_id: int):
    with OdooScannerService(key_index=odoo_access_key_index, login=False) as svc:
        rules = svc.query_putaway_rules_by_product_id(product_id)
    return rules


@barcode.put("/pid/{product_id}/putaway/to_location/{dest_barcode}", response_model=PutawayRule)
def upsert_putaway_rule(product_id: int, dest_barcode: str):
    src_location_id = 8
    with OdooScannerService(key_index=odoo_access_key_index, login=True) as svc:
        loca_data = svc.query_location_by_barcode(dest_barcode)
        if not loca_data:
            logger.error(f"Location with barcode {dest_barcode} not found")
            raise HTTPException(status_code=404, detail=f"Location with barcode {dest_barcode} not found")
        dest_location_id = loca_data['data']['id']
        rule_to_update = PutawayRuleUpdate(
            location_in_id=src_location_id,
            location_out_id=dest_location_id
        )
        rule_ = svc.upsert_putaway_rule_by_product_id(product_id, rule_to_update)
    return rule_


@barcode.get("/delivery_order/{order_number}", response_model=List[Dict])
def query_delivery_order_by_order_number(order_number: str):
    with OdooScannerService(key_index=odoo_access_key_index, login=False) as svc:
        order = svc.query_delivery_order_by_order_number(order_number)
    return order