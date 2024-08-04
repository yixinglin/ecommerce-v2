import os
from typing import List
from fastapi import APIRouter, Query
from sp_api.base import Marketplaces
from starlette.requests import Request
from starlette.responses import StreamingResponse, HTMLResponse, Response
from starlette.templating import Jinja2Templates

import utils.time as utils_time
from core.db import OrderQueryParams
from core.log import logger
from models.pickpack import BatchOrderConfirmEvent
from schemas import BasicResponse, ResponseSuccess
from services.amazon.AmazonService import AmazonOrderService, AmazonService
from services.pickpack.PickPackService import PickPackService, AmazonPickPackService
from utils.stringutils import remove_duplicates, to_german_price, generate_barcode_svg

pp_amazon = APIRouter(prefix="/amazon", tags=['Pick-Pack Services for Amazon'])
pp_common = APIRouter(prefix="/common", tags=['Pick-Pack Services Common'])


@pp_amazon.get("/batch-pick",
               summary="Download a batch-picking slip in Excel format",
               response_class=StreamingResponse, )
def download_batch_pick_slip_by_references_amazon(refs: str = Query(description="Order references separated by semicolon"),
                        api_key_index: int = Query(0, description="Index of API key in settings.API_KEYS list")):
    """
    List GLS Shipments by references
    :param api_key_index:
    :param references:
    :return:
    """
    refs = remove_duplicates(refs.split(";"))
    with AmazonPickPackService(key_index=api_key_index, marketplace=Marketplaces.DE) as svc:
        sr = svc.download_batch_pick_slip_excel(orderIds=refs)
    return sr


@pp_amazon.get("/batch-pack",
               summary="Download a batch-packing slip in Excel format",
               response_class=StreamingResponse, )
def download_pack_slips_excel_amazon(refs: str, api_key_index: int = Query(0,
                                                                           description="Index of API key in settings.API_KEYS list")):
    """
    Download sorted orders excel file. The orders are sorted by order_keys.
    :param refs:
    :return:
    """
    refs = remove_duplicates(refs.split(";"))
    with AmazonPickPackService(key_index=api_key_index, marketplace=Marketplaces.DE) as svc:
        sr = svc.download_pack_slip_excel(orderIds=refs)
    return sr


@pp_amazon.get("/batch-pack/all",
               summary="Download a batch-packing slip in Excel format which includes all orders",
               response_class=StreamingResponse, )
def download_all_orders_excel_amazon(days_ago: int = Query(7, description="Days ago to get unshipped orders"),
                                     api_key_index: int = Query(0,
                                                                description="Index of API key in settings.API_KEYS list")):
    """
    Download all orders excel file
    :return:
    """
    query = OrderQueryParams()
    query.limit = 99999
    query.offset = 0
    query.purchasedDateFrom = utils_time.days_ago(days=days_ago)
    query.status = ["Shipped"]
    with AmazonPickPackService(key_index=api_key_index, marketplace=Marketplaces.DE) as svc:
        sr = svc.download_all_orders_excel(query)
    return sr


@pp_amazon.get("/batch-pack/unshipped",
               summary="Download a batch-packing slip in Excel format which includes all unshipped orders",
               response_class=StreamingResponse, )
def download_unshipped_pack_slips_excel_amazon(
        api_key_index: int = Query(0, description="Index of API key in settings.API_KEYS list"),
        up_to_date: bool = Query(False, description="Save orders from api before returning data"),
        days_ago: int = Query(7, description="Days ago to get unshipped orders")
):
    """
    Download unshipped pack slips excel file
    :return:
    """
    # Get unshipped orders
    with AmazonService(key_index=api_key_index, marketplace=Marketplaces.DE) as man:
        data = man.query_unshipped_amazon_orders(up_to_date=up_to_date, days_ago=days_ago)
        orders = data['orders']
    if len(orders) == 0:
        logger.info("No unshipped orders found.")
        return ResponseSuccess(data=[], size=0, message="No unshipped orders found.")
    refs = remove_duplicates([order.orderId for order in orders])
    with AmazonPickPackService(key_index=api_key_index, marketplace=Marketplaces.DE) as svc:
        data = svc.download_pack_slip_excel(orderIds=refs)
    return data

@pp_amazon.get("/batch-pick/unshipped",
               summary="Download a batch-picking slip in Excel format which includes all unshipped orders",
               response_class=StreamingResponse, )
def download_unshipped_pick_slips_excel_amazon(
        api_key_index: int = Query(0, description="Index of API key in settings.API_KEYS list"),
        up_to_date: bool = Query(False, description="Save orders from api before returning data"),
        days_ago: int = Query(7, description="Days ago to get unshipped orders")
):
    """
    Download unshipped pick slips excel file
    :return:
    """
    with AmazonService(key_index=api_key_index, marketplace=Marketplaces.DE) as man:
        data = man.query_unshipped_amazon_orders(up_to_date=up_to_date, days_ago=days_ago)
        orders = data['orders']
    if len(orders) == 0:
        logger.info("No unshipped orders found.")
        return ResponseSuccess(data=[], size=0, message="No unshipped orders found.")
    refs = remove_duplicates([order.orderId for order in orders])

    with AmazonPickPackService(key_index=api_key_index, marketplace=Marketplaces.DE) as svc:
        data = svc.download_batch_pick_slip_excel(refs)
    return data


@pp_amazon.post("/bulk-ship/gls",
                summary="Create a batch of Gls Shipments by the given order references. "
                        "Filtering out all orders that need transparency code.",
                response_model=BasicResponse[dict])
def bulk_gls_shipments_by_references(refs: List[str]):
    """
    Create a batch of Gls Shipments by the given order references.
    Filtering out all orders that need transparency code.
    Returns a Batch-ID of the bulk-shipment-event.
    :param refs: A list of references
    :return: Data with batchId, orderIds, trackIds, slips, labels, message, length
    TODO 有BUG，需要修复。
    """
    carrier = "gls"
    with AmazonPickPackService(key_index=0, marketplace=Marketplaces.DE) as svc:
        data = svc.bulk_gls_shipments_by_references(refs=refs, carrier=carrier)
    return ResponseSuccess(data=data)


@pp_amazon.get("/pack-slip/html",
               summary="Display a packing slip in  HTML.",
               response_class=HTMLResponse, )
def get_pack_slip_html(request: Request, response: Response,
                       orderId: str,
                       api_key_index: int = Query(0, description="Index of API key in settings.API_KEYS list")):
    """
    Display a standard packing slip in HTML.
    :param orderId:  The order id.
    :param api_key_index:
    :return:
    """
    with AmazonOrderService(key_index=api_key_index, marketplace=Marketplaces.DE) as man_amazon:
        order = man_amazon.find_order_by_id(orderId)

    for item in order.items:
        item.subtotal = to_german_price(item.subtotal)
        item.total = to_german_price(item.total)
        item.tax = to_german_price(item.tax)
        item.unitPrice = to_german_price(item.unitPrice)

    # German datetime format
    time_format = "%d.%m.%Y %H:%M:%S"
    order.purchasedAt = utils_time.datetime_to_date(order.purchasedAt, target_pattern=time_format)
    order.updatedAt = utils_time.datetime_to_date(order.updatedAt, target_pattern=time_format)
    order.createdAt = utils_time.datetime_to_date(order.createdAt, target_pattern=time_format)
    barcode = generate_barcode_svg(order.orderId)

    templates = Jinja2Templates(directory=os.path.join("assets", "templates", "web"))
    return templates.TemplateResponse(name="standard_packslip.html",
                                      request=request,
                                      headers={"Cache-Control": "max-age=3600, public"},
                                      context={"order": order, "barcode": barcode})


@pp_common.get("/batch-ship-event",
               summary="Return batch-order-confirm event with the given batchId.",
               response_model=BasicResponse[BatchOrderConfirmEvent])
def get_batch_order_confirm_event(batchId: str):
    """
    Return batch-order-confirm event with the given batchId.
    The event is created by the bulk-shipments-by-references method.

    TODO: 给这个端口做个React展示页面，显示运单，装箱单，分拣单，拣货单。
    :param batchId:  The batchId of the event.
    :return:  The BatchOrderConfirmEvent object.
    """
    with PickPackService() as man:
        event: BatchOrderConfirmEvent = man.get_batch_order_confirm_event(batchId)
        if event is None:
            return ResponseSuccess(data=None, message="Batch event not found.")
    return ResponseSuccess(data=event)
