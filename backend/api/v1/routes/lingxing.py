import base64
import io
from typing import Optional, List
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse, Response

from core.config2 import settings
from core.log import logger
from external.lingxing.base import FbaShipmentPlanStatus, OrderClient
from schemas import ResponseSuccess, BasicResponse
from services.lingxing import (ListingService, BasicDataService,
                               WarehouseService, FbaShipmentPlanService)
from services.lingxing.ReplenishmentService import WarehouseReplenishmentService, ReplenishmentBasicService, \
    SKUReplenishmentProfileUpdate, AmazonWarehouseReplenishmentService
from services.lingxing.services import GeneralService, LingxingOrderDetail, OrderService
import utils.time as time_utils

warehouse_router = APIRouter(prefix="/warehouse")
listing_router = APIRouter(prefix="/listing")
basic_router = APIRouter(prefix="/basic")
fba_schipment_plans = APIRouter(prefix="/fba-shipment-plans")
order_router = APIRouter(prefix="/order")

key_index = settings.api_keys.lingxing_access_key_index
proxy_index = settings.http_proxy.index


@listing_router.get("/listings",
                    summary="Get all listings",
                    response_model=BasicResponse[dict], )
async def get_all_listings(offset: int = 0, limit: int = 100, seller_id: int = None):
    async with ListingService(key_index, proxy_index) as service:
        filter_ = {}
        if seller_id is not None:
            filter_['data.sid'] = seller_id
        listings = await service.find_all_listings(offset=offset, limit=limit, filter_=filter_)
    data = {
        "listings": listings,
        "length": len(listings)
    }
    return ResponseSuccess(data=data)


@listing_router.get("/id/{listing_id}",
                    summary="Get a listing by id",
                    response_model=BasicResponse[dict], )
async def get_listing_by_id(listing_id: str):
    async with ListingService(key_index, proxy_index) as service:
        listing = await service.find_listing_by_listing_id(listing_id)
    data = listing.dict()
    return ResponseSuccess(data=data)


@listing_router.get("/fnsku",
                    summary="Get a listing by fnsku",
                    response_model=BasicResponse[dict], )
async def get_listing_by_fnsku(sid: int, fnsku: str):
    async with ListingService(key_index, proxy_index) as service:
        listings = await service.find_listings_by_fnsku(fnsku)
        if not listings:
            raise ValueError(f"FNSKU {fnsku} not found.")

        listings = [l for l in listings if l.sid == sid]
        if len(listings) != 1:
            raise RuntimeError(f"FNSKU {fnsku} not found or not unique.")

        # if not listings or len(listings) != 1:
        #     raise RuntimeError("FNSKU not found or not unique")
        data = listings[0].dict()
    return ResponseSuccess(data=data)


@listing_router.get("/printshop/listings",
                    summary="Get all printshop listings",
                    response_model=BasicResponse[dict], )
async def get_printshop_listing_view(offset: int = 0, limit: int = 100,
                                     has_fnsku: bool = True, include_off_sale: bool = False,
                                     seller_id: int = None,
                                     is_unique_fnsku: bool = False):
    wid = 11222
    async with GeneralService(key_index, proxy_index) as service:
        list_vo = await service.get_printshop_listing_view(
            has_fnsku=has_fnsku, include_off_sale=include_off_sale,
            wids=[wid], is_unique_fnsku=is_unique_fnsku, seller_id=seller_id,
            offset=offset, limit=limit)
    data = {
        "list_vo": list_vo,
        "length": len(list_vo)
    }
    return ResponseSuccess(data=data)


@listing_router.get(
    "/download/fnsku-label/{listing_id}",
    response_class=Response,
)
async def get_fnsku_label_by_listing_id(
        listing_id: str,
        quantity: Optional[int] = 1
):
    async with ListingService(key_index, proxy_index) as listing_service:
        async with GeneralService(key_index, proxy_index) as general_service:
            listing = await listing_service.find_listing_by_listing_id(listing_id)
            b64 = await general_service.generate_fnsku_label_by_listing_id(
                listing_id,
                quantity=quantity
            )
    label = base64.b64decode(b64)
    sku = listing.local_sku
    filename = f"{sku}.pdf"
    encoded_filename = quote(filename)

    inline = True
    if inline:
        disposition = f"inline; filename={encoded_filename}.pdf"
    else:
        disposition = f"attachment; filename={encoded_filename}.pdf"

    headers = {
        "Content-Disposition": disposition,
        "Content-Length": str(len(label)),
    }
    logger.info(f"filename: {filename}, disposition: {disposition}")
    return Response(
        content=label,
        media_type="application/pdf",
        headers=headers
    )


@basic_router.get("/sellers",
                  summary="Get all sellers",
                  response_model=BasicResponse[dict], )
async def get_all_sellers():
    async with BasicDataService(key_index, proxy_index) as service:
        sellers = await service.find_all_sellers()
    data = {
        "sellers": sellers,
        "length": len(sellers)
    }
    return ResponseSuccess(data=data)


@warehouse_router.get("/inventory",
                      summary="Get all inventories",
                      response_model=BasicResponse[dict], )
async def get_all_inventories(offset: int = 0, limit: int = 100):
    wid = 11222
    async with WarehouseService(key_index, proxy_index) as service:
        inventories = await service.find_all_inventory_with_bin(wids=[wid],
                                                                offset=offset,
                                                                limit=limit)
    data = {
        "inventories": inventories,
        "length": len(inventories)
    }
    return ResponseSuccess(data=data)


class ReplenishmenetReportRequestBody(BaseModel):
    filename: str


@warehouse_router.post("/replenishment/report",
                       summary="Create replenishment report",
                       response_class=StreamingResponse)
async def create_replenishment_report(body: ReplenishmenetReportRequestBody):
    filename = body.filename
    now_ = time_utils.now(pattern='%Y%m%d')
    async with WarehouseReplenishmentService(key_index, proxy_index) as service:
        df_warehouse_report = await service.create_replenishment_report(filename)

    async with AmazonWarehouseReplenishmentService(key_index, proxy_index) as service:
        df_amazon_report = await service.create_replenishment_report(filename)

    df_reports = {
        "warehouse_report": df_warehouse_report,
        "amazon_report": df_amazon_report
    }

    buffer = service.to_excel(df_reports)
    headers = {
        'Content-Disposition': f'attachment; filename="report_replenishment_{now_}.xlsx"'
    }
    return StreamingResponse(
        buffer,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

class ReplenishmenetProfileImportRequestBody(BaseModel):
    filename: str
    updated_by: str

@warehouse_router.post("/replenishment/profiles/import",
                          response_model=BasicResponse[dict],
                          summary="Import replenishment profiles")
async def import_replenishment_profiles(body: ReplenishmenetProfileImportRequestBody):
    async with ReplenishmentBasicService(key_index, proxy_index) as service:
        filename = body.filename
        updated_by = body.updated_by
        results = await service.import_replenishment_profiles(filename, updated_by)
    return ResponseSuccess(data=results)

@warehouse_router.get("/replenishment/profiles",
    summary="Get replenishment profiles",
    response_model=BasicResponse[dict])
async def get_replenishment_profiles(
    offset: int = 0,
    limit: int = 100,
    brand: Optional[str] = None,
    keyword: Optional[str] = None,
):
    async with ReplenishmentBasicService(key_index, proxy_index) as service:
        results = await service.get_replenishment_profiles(
            offset=offset,
            limit=limit,
            brand=brand,
            keyword=keyword
        )
    return ResponseSuccess(data=results)

@warehouse_router.put("/replenishment/profile/{profile_id}",
                      summary="Update replenishment profile",
                      response_model=BasicResponse[dict])
async def update_replenishment_profile(profile_id: int, update_data: SKUReplenishmentProfileUpdate):
    async with ReplenishmentBasicService(key_index, proxy_index) as service:
        results = await service.update_replenishment_profile(profile_id, update_data)
    return ResponseSuccess(data=results)

@warehouse_router.delete("/replenishment/profile/{profile_id}",
                         summary="Delete replenishment profile",
                         response_model=BasicResponse[dict])
async def delete_replenishment_profile(profile_id: int):
    async with ReplenishmentBasicService(key_index, proxy_index) as service:
        results = await service.delete_replenishment_profile(profile_id)
    return ResponseSuccess(data=results)

@warehouse_router.get("/replenishment/profile/filters",
                       summary="Get replenishment profile filters",
                       response_model=BasicResponse[dict])
async def get_replenishment_profile_filters():
    async with ReplenishmentBasicService(key_index, proxy_index) as service:
        filters = await service.get_replenishment_profile_filters()
    return ResponseSuccess(data=filters)

@fba_schipment_plans.get("/plans", summary="Get all FBA shipment plans",
                         deprecated=True,
                         response_model=BasicResponse[dict], )
async def get_fba_shipment_plans(reduced: bool = False, offset: int = 0, limit: int = 100):
    async with GeneralService(key_index, proxy_index) as service:
        if reduced:
            statuses = [FbaShipmentPlanStatus.Placed]
        else:
            statuses = None
        fba_shipment_plans = await service.get_fba_shipment_plans_view(statuses=statuses, offset=offset, limit=limit)
    data = {
        "plans": fba_shipment_plans,
        "length": len(fba_shipment_plans)
    }
    return ResponseSuccess(data=data)

@order_router.get("/details/download", summary="Download LingXing order details",
                 response_class=StreamingResponse)
async def download_lingxing_order_details(is_business_order: bool = True):
    async with OrderService(key_index, proxy_index) as service:
        orders = await service.find_order_details(is_business_order=is_business_order)
        df = pd.DataFrame([o.dict() for o in orders])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        headers = {
            'Content-Disposition': 'attachment; filename="order_details.xlsx"'
        }
        return StreamingResponse(
            buffer,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
