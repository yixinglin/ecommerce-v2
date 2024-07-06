from io import BytesIO
from typing import List

from fastapi import APIRouter, Query
from sp_api.base import Marketplaces
from starlette.responses import StreamingResponse
import utils.time as utils_time
from core.config import settings
from core.log import logger
from rest.amazon.DataManager import AmazonOrderMongoDBManager
from rest.pickpack.DataManager import PickPackMongoDBManager
from schemas import BasicResponse, ResponseSuccess
from utils.stringutils import remove_duplicates
from vo.carriers import PickSlipItemVO

pp_amazon = APIRouter(prefix="/amazon", tags=['Pick-Pack Services for Amazon'])


@pp_amazon.get("/pick-items",
               summary="Pick Items by sku.",
               response_model=BasicResponse[List[PickSlipItemVO]])
def get_pick_items_by_references_amazon(refs: str):
    refs = remove_duplicates(refs.split(";"))
    with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                       key_index=0, marketplace=Marketplaces.DE) as man1:
            orders = man1.find_orders_by_ids(refs)
            vo = man.get_pick_items(orders)
    return ResponseSuccess(data=vo, size=len(vo))


@pp_amazon.get("/batch-pick", summary="Batch Pick Slip",
               response_class=StreamingResponse, )
def download_batch_pick_slip_by_references_amazon(refs: str):
    """
    List GLS Shipments by references
    :param references:
    :return:
    """
    refs = remove_duplicates(refs.split(";"))
    with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=0, marketplace=Marketplaces.DE) as man:
        orders = man.find_orders_by_ids(refs)
    with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        excel_bytes = man.pick_slip_to_excel(orders)
    filename = f"Batch_PICK_SLIPS_{utils_time.now(pattern='%Y%m%d_%H%M')}"
    filesize = len(excel_bytes)
    headers = {'Content-Disposition': f'inline; filename="{filename}.xlsx"', 'Content-Length': str(filesize)}
    return StreamingResponse(BytesIO(excel_bytes),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers=headers)


@pp_amazon.get("/pack-items", summary="Pack Items",
               response_class=StreamingResponse, )
def download_pack_slips_excel_amazon(refs: str):
    """
    Download sorted orders excel file. The orders are sorted by order_keys.
    :param refs:
    :return:
    """
    refs = remove_duplicates(refs.split(";"))
    with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=0, marketplace=Marketplaces.DE) as man1:
        with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man2:
            orders = man1.find_orders_by_ids(refs)
            refs = man2.sort_packing_orders(orders)
            orders = man1.find_orders_by_ids(refs)
            excel_bytes = man2.pack_slips_to_excel(orders)
    filename = f"PACK_SLIPS_{utils_time.now(pattern='%Y%m%d_%H%M')}"
    filesize = len(excel_bytes)
    headers = {'Content-Disposition': f'inline; filename="{filename}.xlsx"',
               'Content-Length': str(filesize)}
    return StreamingResponse(BytesIO(excel_bytes),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers=headers)


@pp_amazon.get("/pack-items/unshipped", summary="Pack Unshipped Items",
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
    # TODO: Get unshipped orders
    with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=api_key_index, marketplace=Marketplaces.DE) as man:
        orders = man.find_unshipped_orders(days_ago=days_ago, up_to_date=up_to_date)
    if len(orders) == 0:
        logger.info("No unshipped orders found.")
        return ResponseSuccess(data=[], size=0, message="No unshipped orders found.")
    refs = remove_duplicates([order.orderId for order in orders])
    return download_pack_slips_excel_amazon(";".join(refs))


@pp_amazon.get("/pick-items/unshipped", summary="Pick Unshipped Items",
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
    with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=api_key_index, marketplace=Marketplaces.DE) as man:
        orders = man.find_unshipped_orders(days_ago=days_ago, up_to_date=up_to_date)
    if len(orders) == 0:
        logger.info("No unshipped orders found.")
        return ResponseSuccess(data=[], size=0, message="No unshipped orders found.")
    refs = remove_duplicates([order.orderId for order in orders])
    return download_batch_pick_slip_by_references_amazon(";".join(refs))
