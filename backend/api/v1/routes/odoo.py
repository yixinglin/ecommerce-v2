import io
from typing import List

import pandas as pd
from fastapi import APIRouter, Body
from starlette.responses import StreamingResponse, HTMLResponse
from core.config2 import settings
from core.log import logger
from schemas import ResponseSuccess, BasicResponse
from schemas.vip import VipOrder, VipCustomer, PimProduct, CrmAddress, CrmContact
from services.odoo.OdooDashboardService import OdooOrderDashboardService
from services.odoo.OdooInventoryService import OdooInventoryService
from services.odoo.OdooOrderService import OdooProductService, OdooContactService, OdooOrderService, OdooHsmsService
from services.odoo.OdooStatistics import OdooStatisticsService

odoo_inventory = APIRouter(prefix="/inventory",)
odoo_sales = APIRouter(prefix="/sales", )
odoo_contact = APIRouter(prefix="/contact", )
odoo_dashboard = APIRouter(prefix="/dashboard", )
odoo_hsms = APIRouter(prefix="/hsms", )

odoo_access_key_index = settings.api_keys.odoo_access_key_index

@odoo_contact.get('/addresses')
def get_odoo_contact_list():
    #  Odoo Contact List API
    with OdooContactService(key_index=odoo_access_key_index, login=False) as svc:
        data = svc.query_all_contact_shipping_addresses(offset=0, limit=10000)
    return ResponseSuccess(data=data)

@odoo_contact.get(
    '/{id}/vip',
    response_model=BasicResponse[VipCustomer])
def get_vip_customer_from_odoo_contact_by_id(id: int):
    #  Odoo Contact
    with OdooContactService(key_index=odoo_access_key_index, login=False) as svc:
        data = svc.query_contact_by_id(id)

    false_to_str = lambda x: x if x else ""
    is_company = data.get("is_company", False)
    if is_company:
        company_name = false_to_str(data.get("name", ""))
        contact = ""
    else:
        company_name = ""
        contact = false_to_str(data.get("name", ""))
    street = false_to_str(data.get("street", ""))
    street2 = false_to_str(data.get("street2", ""))
    zip = false_to_str(data.get("zip", ""))
    city = false_to_str(data.get("city", ""))
    country_id = data.get("country_id", None)
    country = country_id[1] if country_id else ""
    country = country.replace("Germany", "Deutschland")

    vip_customer = VipCustomer(
        companyName=company_name,
        contact=contact,
        address=f"{street}, {zip} {city}, {country}",
        addressLine2=street2,
        zip=false_to_str(data.get("zip", "")),
        phone=false_to_str(data.get("phone", "")),
        mobile=false_to_str(data.get("mobile", "")),
        email=false_to_str(data.get("email", "")),
    )

    return ResponseSuccess(data=vip_customer)


@odoo_sales.post('/orders', summary="Create an Odoo sales order",
                 response_model=BasicResponse[dict])
def create_odoo_order(order: VipOrder=
                      Body(None, description="VIP Order Body"),
                      ):
    logger.info(f"Creating Order: {order.dict()}")
    try:
        with OdooOrderService(key_index=odoo_access_key_index) as svc:
            ans = svc.create_sales_order(order)
    except RuntimeError as e:
        logger.error(f"Order Creation Failed: {e}")
        raise RuntimeError(e)
    return ResponseSuccess(data=ans)


@odoo_hsms.post('/products/pim_product', summary="Create an Odoo product from PIM",
                 response_model=BasicResponse[dict])
def create_odoo_product_from_pim(
        pim_product: PimProduct = Body(None, description="PIM Product Body")
):
    logger.info(f"Creating Product: {pim_product.dict()}")
    try:
        svc = OdooHsmsService(key_index=0, login=True)
        ans = svc.create_product_from_pim(pim_product)
    except RuntimeError as e:
        logger.error(f"Product Creation Failed: {e}")
        raise RuntimeError(e)
    return ResponseSuccess(data=ans)

@odoo_hsms.post('/crm/address', summary="Create an Odoo company from CRM",
                response_model=BasicResponse[dict])
def create_odoo_company_from_crm(
        crm_company: CrmAddress = Body(None, description="CRM Company Body")
):
    logger.info(f"Creating Company: {crm_company.dict()}")
    try:
        svc = OdooHsmsService(key_index=0, login=True)
        ans = svc.create_company_from_crm(crm_company, fill_custom_fields=False)
    except RuntimeError as e:
        logger.error(f"Company Creation Failed: {e}")
        raise RuntimeError(e)
    return ResponseSuccess(data=ans)

@odoo_hsms.post('/crm/contact_person/{address_code}', summary="Create an Odoo contact person from CRM",
                response_model=BasicResponse[dict])
def create_odoo_contact_person_from_crm(
        address_code: str,
        crm_persons: List[CrmContact] = Body(None, description="CRM Contact Body"),
):
    logger.info(f"Creating Contact Persons for {address_code}: {[p.lastName for p in crm_persons]}")
    try:
        svc = OdooHsmsService(key_index=0, login=True)
        ans = svc.create_contact_person_from_crm(address_code, crm_persons, fill_custom_fields=False)
    except RuntimeError as e:
        logger.error(f"Contact Person Creation Failed: {e}")
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


@odoo_dashboard.post('/sales_order_report',
                    summary="Download Sales Order Report")
def download_sales_order_report(days_ago: int = 365):
    salesman_ids = [7]
    with OdooOrderDashboardService(key_index=odoo_access_key_index, login=False) as svc:
        df_report1 = svc.stats_sales_order_by_salesman(salesman_ids, days_ago=days_ago)
        df_report2 = svc.stats_sales_order_by_customer(days_ago=days_ago)
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        df_report1.to_excel(writer, sheet_name='sheet1', index=False)
        df_report2.to_excel(writer, sheet_name='sheet2', index=False)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Sales Order Report.xlsx"}
    )

@odoo_dashboard.post('/sales_order_report/bubble_chart',
                    summary="Render Sales Order Report Bubble Chart",
                    response_class=HTMLResponse)
def render_sales_order_report_bubble_chart(days_ago: int = 365):
    with OdooOrderDashboardService(key_index=odoo_access_key_index, login=False) as svc:
        html = svc.stats_sales_order_by_customer_bubble_chart(days_ago=days_ago)
    return HTMLResponse(html)


# 销量统计
@odoo_dashboard.post('/sales_volume_report',
                    summary="Get Sales Volume Report")
def download_sales_volume_count():
    service = OdooStatisticsService(key_index=odoo_access_key_index)
    df_sales = service.product_sales_report()
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        df_sales.to_excel(writer, sheet_name='sheet1', index=False)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Sales Volume Report.xlsx"}
    )