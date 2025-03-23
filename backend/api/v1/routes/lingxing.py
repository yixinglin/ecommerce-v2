import base64
import io
from urllib.parse import quote

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from core.config2 import settings
from external.lingxing.base import FbaShipmentPlanStatus
from schemas import ResponseSuccess, BasicResponse
from services.lingxing import (ListingService, BasicDataService,
                               WarehouseService, FbaShipmentPlanService)
from services.lingxing.services import GeneralService

warehouse_router = APIRouter(prefix="/warehouse")
listing_router = APIRouter(prefix="/listing")
basic_router = APIRouter(prefix="/basic")
fba_schipment_plans = APIRouter(prefix="/fba-shipment-plans")

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


@listing_router.get("/download/fnsku-label/{listing_id}")
async def get_fnsku_label_by_listing_id(listing_id: str):
    async with ListingService(key_index, proxy_index) as listing_service:
        async with GeneralService(key_index, proxy_index) as general_service:
            listing = await listing_service.find_listing_by_listing_id(listing_id)
            b64 = await general_service.generate_fnsku_label_by_listing_id(listing_id)
    label = base64.b64decode(b64)
    sku = listing.local_sku
    pdf_stream = io.BytesIO(label)
    filename = f"{sku}.pdf"
    encoded_filename = quote(filename)

    embedded = True
    content_disposition = "inline" if embedded else "attachment"
    headers = {
        "Content-Disposition": f"{content_disposition}; filename*=UTF-8\'\'{encoded_filename}",
        "Content-Length": str(len(label)),
    }
    return StreamingResponse(pdf_stream, media_type="application/pdf", headers=headers)


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


@fba_schipment_plans.get("/plans", summary="Get all FBA shipment plans",
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
