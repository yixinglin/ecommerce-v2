from io import BytesIO
from typing import List

from fastapi import APIRouter
from starlette.responses import StreamingResponse
import utils.time as utils_time
from core.config import settings
from rest.common.summary import PickPackDataManager
from rest.pickpack.DataManager import PickPackMongoDBManager
from schemas import BasicResponse, ResponseSuccess
from vo.carriers import PickSlipItemVO

pickpack = APIRouter(prefix="/pickpack", tags=['Pick-Pack Services'])


@pickpack.get("/pick-items",
              summary="Pick Items by sku.",
         response_model=BasicResponse[List[PickSlipItemVO]])
def get_pick_items_by_references(refs: str):

    refs = refs.split(";")
    with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        vo = man.get_pick_items_by_references(refs)
    return ResponseSuccess(data=vo, size=len(vo))


@pickpack.get("/batch-pick", summary="Batch Pick Slip",
         response_class=StreamingResponse,)
def download_batch_pick_slip_by_references(refs: str):
    """
    List GLS Shipments by references
    :param references:
    :return:
    """
    refs = refs.split(";")
    with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        excel_bytes = man.pick_slip_to_excel(refs)
    filename = f"Batch_PICK_SLIPS_{utils_time.now(pattern='%Y%m%d_%H%M')}"
    headers = {'Content-Disposition': f'inline; filename="{filename}.xlsx"'}
    return StreamingResponse(BytesIO(excel_bytes),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers=headers)

@pickpack.get("/pack-items", summary="Pack Items",
              response_class=StreamingResponse,)
def download_sorted_pack_slips_excel(refs: str):
    """
    Download sorted orders excel file
    :param refs:
    :return:
    """
    refs = refs.split(";")
    with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        refs = man.sort_packing_order_refs(refs)
        excel_bytes = man.pack_slips_to_excel(refs)
    filename = f"PACK_SLIPS_{utils_time.now(pattern='%Y%m%d_%H%M')}"
    headers = {'Content-Disposition': f'inline; filename="{filename}.xlsx"'}
    return StreamingResponse(BytesIO(excel_bytes),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers=headers)

@pickpack.get("/pack-items/unshipped", summary="Pack Unshipped Items",
              response_class=StreamingResponse,)
def download_unshipped_pack_slips_excel():
    """
    Download unshipped pack slips excel file
    :return:
    """

    with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        orders = man.find_unshipped_amazon_orders()
        refs = [order.orderId for order in orders]
    return download_sorted_pack_slips_excel(";".join(refs))

@pickpack.get("/pick-items/unshipped", summary="Pick Unshipped Items",
              response_class=StreamingResponse,)
def download_unshipped_pick_slips_excel():
    """
    Download unshipped pick slips excel file
    :return:
    """
    with PickPackMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        orders = man.find_unshipped_amazon_orders()
        refs = [order.orderId for order in orders]
    return download_batch_pick_slip_by_references(";".join(refs))

