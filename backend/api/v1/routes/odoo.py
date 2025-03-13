from fastapi import APIRouter, Body, HTTPException
from core.config2 import settings
from core.log import logger
from schemas import ResponseSuccess, BasicResponse, ResponseFailure, ResponseNotFound
from schemas.vip import VipOrder
from services.odoo.OdooInventoryService import OdooInventoryService
from services.odoo.OdooOrderService import OdooProductService, OdooContactService, OdooOrderService

odoo_inventory = APIRouter(prefix="/inventory",)
odoo_sales = APIRouter(prefix="/sales", )
odoo_contact = APIRouter(prefix="/contact", )

odoo_access_key_index = settings.api_keys.odoo_access_key_index

@odoo_contact.get('/addresses')
def get_odoo_contact_list():
    #  Odoo Contact List API
    with OdooContactService(key_index=odoo_access_key_index, login=False) as svc:
        data = svc.query_all_contact_shipping_addresses(offset=0, limit=10000)
    return ResponseSuccess(data=data)

@odoo_sales.post('/orders', summary="Create an Odoo sales order",
                 response_model=BasicResponse[dict])
def create_odoo_order(order: VipOrder=
                      Body(None, description="Odoo Order Body"),
                      ):
    logger.info(f"Creating Order: {order.dict()}")
    try:
        with OdooOrderService(key_index=odoo_access_key_index) as svc:
            ans = svc.create_sales_order(order)
    except RuntimeError as e:
        logger.error(f"Order Creation Failed: {e}")
        raise RuntimeError(e)
    return ResponseSuccess(data=ans)

@odoo_inventory.get('/products')
def get_odoo_product_list():
    # Implement Odoo Product List API
    with OdooProductService(key_index=odoo_access_key_index, login=False) as svc:
        # data = svc.query_all_product_templates(offset=0, limit=10000)
        data = svc.query_all_products(offset=0, limit=10000)
    return ResponseSuccess(data=data)

@odoo_inventory.get('/quants')
def get_odoo_quant_list():
    # Odoo Quant List API
    with OdooInventoryService(key_index=odoo_access_key_index, login=False) as svc:
        data = svc.query_all_quants(offset=0, limit=10000)
    return ResponseSuccess(data=data)

@odoo_inventory.get('/locations')
def get_odoo_location_list():
    #  Odoo Location List API
    with OdooInventoryService(key_index=odoo_access_key_index, login=False) as svc:
        data = svc.query_all_locations(offset=0, limit=10000)
    return ResponseSuccess(data=data)


@odoo_inventory.get('/delivery_order/{order_number}',
                    summary="Get Odoo Delivery Order by Order Number",
                    response_model=BasicResponse[dict])
def get_odoo_delivery_order(order_number: str):
    with OdooOrderService(key_index=odoo_access_key_index, login=False) as svc:
        data = svc.query_delivery_order_by_order_number(order_number)
    return ResponseSuccess(data=data)

