import os
from io import BytesIO
from typing import List

from fastapi import APIRouter, Query, Body
from sp_api.base import Marketplaces
from starlette.requests import Request
from starlette.responses import StreamingResponse, HTMLResponse, Response
from starlette.templating import Jinja2Templates
import utils.utilpdf as utilpdf
import utils.time as utils_time
from core.db import OrderQueryParams
from core.log import logger
from models.pickpack import BatchOrderConfirmEvent
from rest.amazon.DataManager import AmazonOrderMongoDBManager
from rest.amazon.bulkOrderService import AmazonBulkPackSlipDE
from rest.pickpack.DataManager import PickPackMongoDBManager
from schemas import BasicResponse, ResponseSuccess
from utils.stringutils import remove_duplicates, to_german_price, generate_barcode_svg
import utils.stringutils as stringutils

pp_amazon = APIRouter(prefix="/amazon", tags=['Pick-Pack Services for Amazon'])
pp_common = APIRouter(prefix="/common", tags=['Pick-Pack Services Common'])


# @pp_amazon.get("/pick-items",
#                summary="Pick Items by sku.",
#                response_model=BasicResponse[List[PickSlipItemVO]])
# def get_pick_items_by_references_amazon(refs: str):
#     refs = remove_duplicates(refs.split(";"))
#     with PickPackMongoDBManager() as man:
#         with AmazonOrderMongoDBManager(key_index=0, marketplace=Marketplaces.DE) as man1:
#             orders = man1.find_orders_by_ids(refs)
#             vo = man.get_pick_items(orders)
#     return ResponseSuccess(data=vo, size=len(vo))


@pp_amazon.get("/batch-pick", summary="Download a batch-picking slip in Excel format",
               response_class=StreamingResponse, )
def download_batch_pick_slip_by_references_amazon(refs: str):
    """
    List GLS Shipments by references
    :param references:
    :return:
    """
    refs = remove_duplicates(refs.split(";"))
    with AmazonOrderMongoDBManager(key_index=0, marketplace=Marketplaces.DE) as man_amz:
        orders = man_amz.find_orders_by_ids(refs)
    with PickPackMongoDBManager() as man_pp:
        excel_bytes = man_pp.pick_slip_to_excel(orders)
    filename = f"Batch_PICK_SLIPS_{utils_time.now(pattern='%Y%m%d_%H%M')}"
    filesize = len(excel_bytes)
    headers = {'Content-Disposition': f'inline; filename="{filename}.xlsx"', 'Content-Length': str(filesize)}
    return StreamingResponse(BytesIO(excel_bytes),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers=headers)

@pp_amazon.get("/batch-pack", summary="Download a batch-packing slip in Excel format",
               response_class=StreamingResponse, )
def download_pack_slips_excel_amazon(refs: str):
    """
    Download sorted orders excel file. The orders are sorted by order_keys.
    :param refs:
    :return:
    """
    refs = remove_duplicates(refs.split(";"))
    with AmazonOrderMongoDBManager(key_index=0, marketplace=Marketplaces.DE) as man_amz:
        with PickPackMongoDBManager() as man_pp:
            orders = man_amz.find_orders_by_ids(refs)
            refs = man_pp.sort_packing_orders(orders)
            orders = man_amz.find_orders_by_ids(refs)
            excel_bytes = man_pp.pack_slips_to_excel(orders)
    filename = f"PACK_SLIPS_{utils_time.now(pattern='%Y%m%d_%H%M')}"
    filesize = len(excel_bytes)
    headers = {'Content-Disposition': f'inline; filename="{filename}.xlsx"',
               'Content-Length': str(filesize)}
    return StreamingResponse(BytesIO(excel_bytes),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers=headers)

@pp_amazon.get("/batch-pack/all",
               summary="Download a batch-packing slip in Excel format which includes all orders",
               response_class=StreamingResponse, )
def download_all_orders_excel_amazon(days_ago: int = Query(7, description="Days ago to get unshipped orders")):
    """
    Download all orders excel file
    :return:
    """
    api_key_index = 0
    with AmazonOrderMongoDBManager(key_index=api_key_index, marketplace=Marketplaces.DE) as man:
        query = OrderQueryParams()
        query.limit = 99999
        query.offset = 0
        query.purchasedDateFrom = utils_time.days_ago(days=days_ago)
        query.status = ["Shipped"]
        orders = man.find_orders_by_query_params(query)
    if len(orders) == 0:
        logger.info("No orders found.")
        return ResponseSuccess(data=[], size=0, message="No orders found.")
    refs = remove_duplicates([order.orderId for order in orders])
    return download_pack_slips_excel_amazon(";".join(refs))

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
    with AmazonOrderMongoDBManager(key_index=api_key_index, marketplace=Marketplaces.DE) as man:
        orders = man.find_unshipped_orders(days_ago=days_ago, up_to_date=up_to_date)
    if len(orders) == 0:
        logger.info("No unshipped orders found.")
        return ResponseSuccess(data=[], size=0, message="No unshipped orders found.")
    refs = remove_duplicates([order.orderId for order in orders])
    return download_pack_slips_excel_amazon(";".join(refs))

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
    with AmazonOrderMongoDBManager(key_index=api_key_index, marketplace=Marketplaces.DE) as man:
        orders = man.find_unshipped_orders(days_ago=days_ago, up_to_date=up_to_date)
    if len(orders) == 0:
        logger.info("No unshipped orders found.")
        return ResponseSuccess(data=[], size=0, message="No unshipped orders found.")
    refs = remove_duplicates([order.orderId for order in orders])
    return download_batch_pick_slip_by_references_amazon(";".join(refs))


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
    refs = remove_duplicates(refs)
    with PickPackMongoDBManager() as man_pp:
        with AmazonOrderMongoDBManager(key_index=0, marketplace=Marketplaces.DE) as man_amazon:
            orders = man_amazon.find_orders_by_ids(refs)
            # Filter out orders that need transparency code
            orders = [o for o in orders if not man_amazon.need_transparency_code(o)]
            # Number of orders to be shipped
            num_orders = len(orders)
            batchId = man_pp.generate_batch_id("AMZ")
            batchEvent = man_pp.bulk_shipment_for_orders(orders=orders, batchId=batchId, carrier=carrier,
                                                         sort_by_order_key=True)
            # Create pack slip for the batch using the original template of Amazon
            packSlip = AmazonBulkPackSlipDE.add_packslip_to_container(orderIds=batchEvent.orderIds)
            batchEvent.packSlipB64 = stringutils.base64_encode_str(packSlip)
            man_pp.cache_batch_event(batchEvent)

    data = {
        "batchId": batchEvent.batchId,
        "orderIds": batchEvent.orderIds,
        "trackIds": batchEvent.shipmentIds,
        "message": f"GLS shipments of {num_orders} orders created successfully.\n" + batchEvent.message,
        "length": len(batchEvent.orderIds)
    }

    return ResponseSuccess(data=data)


@pp_amazon.get("/pack-slip/html",
               summary="Display a packing slip in  HTML.",
               response_class=HTMLResponse, )
def get_pack_slip_html(request: Request, response: Response,
                       orderId: str):
    with AmazonOrderMongoDBManager(key_index=0, marketplace=Marketplaces.DE) as man_amazon:
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

    TODO: 给这个端口做个React展示页面，显示运单，装箱单，分拣单，拣货单。
    :param batchId:  The batchId of the event.
    :return:  The BatchOrderConfirmEvent object.
    """
    with PickPackMongoDBManager() as man:
        event: BatchOrderConfirmEvent = man.get_batch_order_confirm_event(batchId)
        if event is None:
            return ResponseSuccess(data=None, message="Batch event not found.")
    return ResponseSuccess(data=event)
