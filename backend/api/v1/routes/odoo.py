from fastapi import APIRouter, Body, HTTPException
from core.config import settings
from core.log import logger
from schemas import ResponseSuccess, BasicResponse
from schemas.vip import VipOrder
from services.odoo.OdooInventoryService import OdooInventoryService
from services.odoo.OdooOrderService import OdooProductService, OdooContactService, OdooOrderService

odoo_inventory = APIRouter(prefix="/inventory",)
odoo_sales = APIRouter(prefix="/sales", )
odoo_contact = APIRouter(prefix="/contact", )


@odoo_contact.get('/contacts')
def get_odoo_contact_list():
    # TODO: Implement Odoo Contact List API
    with OdooContactService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        data = svc.query_all_contacts(offset=0, limit=10000)
    return ResponseSuccess(data=data)

@odoo_sales.post('/orders', summary="Create an Odoo sales order",
                 response_model=BasicResponse[dict])
def create_odoo_order(order: VipOrder=
                      Body(None, description="Odoo Order Body"),
                      ):
    logger.info(f"Creating Order: {order.dict()}")
    try:
        with OdooOrderService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
            ans = svc.create_order(order)
    except RuntimeError as e:
        logger.error(f"Order Creation Failed: {e}")
        raise RuntimeError(e)
    return ResponseSuccess(data=ans)

@odoo_inventory.get('/products')
def get_odoo_product_list():
    # TODO: Implement Odoo Product List API
    with OdooProductService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        data = svc.query_all_product_templates(offset=0, limit=10000)
    return ResponseSuccess(data=data)

@odoo_inventory.get('/quants')
def get_odoo_quant_list():
    # TODO: Implement Odoo Quant List API
    with OdooInventoryService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        data = svc.query_all_quants(offset=0, limit=10000)
    return ResponseSuccess(data=data)

@odoo_inventory.get('/locations')
def get_odoo_location_list():
    # TODO: Implement Odoo Location List API
    with OdooInventoryService(key_index=settings.ODOO_ACCESS_KEY_INDEX) as svc:
        data = svc.query_all_locations(offset=0, limit=10000)
    return ResponseSuccess(data=data)

