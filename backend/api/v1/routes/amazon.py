import os
from typing import Any, List

from fastapi import APIRouter, Request, Response, Query, Body, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sp_api.base import Marketplaces

import utils.time as time_utils
from core.db import RedisDataManager
from external.amazon.base import AmazonSpAPIKey
from schemas import ResponseSuccess
from schemas.amazon import DailySalesCountVO, PackSlipRequestBody
from schemas.basic import BasicResponse, ResponseNotFound
from services.amazon.AmazonService import AmazonService, FbaService

amz_order = APIRouter(tags=['AMAZON Services'])


@amz_order.get("/orders",
               summary="Get Amazon orders",
               response_model=BasicResponse[dict])
def get_amazon_orders(days_ago: int = Query(7, description="Fetch data for the last x days"),
                      status: List[str] = Query(None, description="Filter orders by status"),
                      offset: int = Query(0, description="Offset for pagination"),
                      limit: int = Query(100, description="Limit for pagination"),
                      api_key_index: int = Query(0, description="Index of API key in settings.API_KEYS list"),
                      ):
    marketplace = Marketplaces.DE
    with AmazonService(key_index=api_key_index, marketplace=marketplace) as svc:
        data = svc.query_amazon_orders(days_ago=days_ago, status=status,
                                       offset=offset, limit=limit,
                                       up_to_date=False)
    return ResponseSuccess(data=data)


@amz_order.get("/orders/ordered-items-count/daily/{days_ago}",
               summary="Get daily ordered items count",
               response_model=BasicResponse[List[DailySalesCountVO]])
def get_daily_ordered_items_count(response: Response,
                                  days_ago: int = Path(description="Fetch data for the last x days"),
                                  country: str = Query("DE", description="Marketplace ")) -> Any:
    marketplace = AmazonSpAPIKey.name_to_marketplace(country)
    with AmazonService(key_index=0, marketplace=marketplace) as svc:
        daily_sales_vo = svc.sum_daily_ordered_items(days_ago=days_ago)
    return ResponseSuccess(data=daily_sales_vo, )


# Show daily ordered items count using html template
@amz_order.get("/orders/ordered-items-count/daily/{days_ago}/treeview",
               summary="Get daily ordered items count in html format",
               response_class=HTMLResponse, )
def view_daily_ordered_items_count_html(request: Request, response: Response,
                                        days_ago: int = Path(description="Fetch data for the last x days"),
                                        country: str = Query("DE",
                                                             description="Marketplace to use (DE, UK, US"), ) -> Any:
    data = get_daily_ordered_items_count(days_ago=days_ago, response=response, country=country)
    templates = Jinja2Templates(directory=os.path.join("assets", "templates", "web"))
    return templates.TemplateResponse(name="AmazonDailySalesCount.html",
                                      request=request,
                                      headers={"Cache-Control": "max-age=3600, public"},
                                      context={"data": data.data})


@amz_order.get("/orders/unshipped",
               summary="Get unshipped order numbers",
               response_model=BasicResponse[dict])
def get_unshipped_order_numbers(country: str = Query("DE", description="Country of the marketplace"),
                                up_to_date: bool = Query(False,
                                                         description="Save orders from api before returning data"),
                                api_key_index: int = Query(0, description="Index of API key in settings.API_KEYS list"),
                                ) -> List[str]:
    """
    Get Amazon order numbers that have unshipped items. The order numbers are sorted by sku.
    :country: Country code that is used to determine a marketplace.
    :return:  List of Amazon order numbers that have unshipped items

    """
    marketplace = AmazonSpAPIKey.name_to_marketplace(country)
    with AmazonService(key_index=api_key_index, marketplace=marketplace) as svc:
        data = svc.query_unshipped_order_numbers(up_to_date=up_to_date)
    return ResponseSuccess(data=data)


@amz_order.get("/orders/sc-urls",
               summary="Get seller central urls",
               response_model=BasicResponse[dict])
def get_seller_central_urls():
    urls = {
        "bulk-confirm-shipment": "https://sellercentral.amazon.de/orders-v3/bulk-confirm-shipment",
        "packing-slip": "https://sellercentral.amazon.de/orders/packing-slip"
    }
    return ResponseSuccess(data=urls)


# http://127.0.0.1:5018/api/v1/amazon/orders/catalog-attributes?api_key_index=0&country=DE&asins=B09FKWS793&asins=B01HTH3C8S
@amz_order.get("/orders/catalog-attributes",
               summary="Get Amazon catalog attributes",
               response_model=BasicResponse[dict])
def get_amazon_catalog_attributes(api_key_index: int = Query(0, description="Index of API key in settings.API_KEYS list"),
                                  country: str = Query("DE", description="Country of the marketplace"),
                                  asins: List[str] = Query(None, description="ASIN of the product to get catalog attributes for")):
    marketplace = AmazonSpAPIKey.name_to_marketplace(country)
    catalog_attrs = []
    with AmazonService(key_index=api_key_index, marketplace=marketplace) as svc:
        for asin in asins:
            svc.catalog_service.save_catalog(asin)
            c_attr = svc.get_catalog_attributes(asin)
            catalog_attrs.append(c_attr)
    return ResponseSuccess(data={
        "catalog_attributes": catalog_attrs
    })

@amz_order.post("/orders/packslip/parse",
                summary="Parse Amazon packing slip and extract all shipments.",
                response_model=BasicResponse[dict])
def parse_amazon_pack_slip_html(
        body: PackSlipRequestBody = Body(None, description="Packing slip data in html format")
):
    """
    Parse Amazon packing slip and extract all shipping addresses, store it to MongoDB.
    Also cache the packing slip data to Redis for 12 hours.
    :param html:
    :param country: Country code using to filtering the packing slips
    :param format: csv, json
    :return: A list of StandardOrder objects.
    """
    formatIn = body.formatIn
    format_ = body.formatOut
    country = body.country
    html_content = body.data
    marketplace = AmazonSpAPIKey.name_to_marketplace(country)
    with AmazonService(key_index=0, marketplace=marketplace) as svc:
        data = svc.parse_amazon_pack_slip_page(html_content, formatIn)
    return ResponseSuccess(data=data)


@amz_order.post("/orders/packslip/cache",
                summary="Upload Amazon packing slip and store it to Redis.",
                response_model=BasicResponse[dict])
async def upload_amazon_pack_slip_redis(request: Request,):
    html_content = await request.body()    # html content in bytes
    html_content = html_content.decode('utf-8') # convert bytes to string
    TIME_TO_LIVE_SEC = 3600 * 48  # 48 hours
    man = RedisDataManager()
    KEY = f"AMZPS:{time_utils.now(pattern='%Y%m%d%H%M%S')}"
    man.set(KEY, html_content, time_to_live_sec=TIME_TO_LIVE_SEC)
    data = {
        "key": KEY,
        "message": "Packing slip has been successfully uploaded to Redis.",
        "timeToLiveSec": TIME_TO_LIVE_SEC,
        "length": 1,
    }
    return ResponseSuccess(data=data)

@amz_order.get("/orders/packslip/uncache",
            summary="Delete Amazon packing slip from Redis cache.",
            response_class=HTMLResponse,
               )
def download_amazon_pack_slip_redis(
        key: str = Query(None, description="Packing slip key in Redis to uncache data")
    ):
    man = RedisDataManager()
    content = man.get(key)  # html content
    if content is None:
        return ResponseNotFound(message=f"Packing slip with key {key} not found in Redis cache.")
    return content


@amz_order.get("/orders/fba/pack-rule",
               summary="Get FBA packing rule",
               response_model=BasicResponse[dict])
def calc_fba_packing_rule(qty: int, sku: str, max_capacity: int):
    with FbaService() as fba_svc:
        rule = fba_svc.fba_packing_rule(qty, sku, max_capacity)
        fba_svc.cache_fba_max_ctn_capacity(sku, max_capacity)
    return ResponseSuccess(data=rule)

@amz_order.get("/orders/fba/max-ctn-capacity/{sku}",
               summary="Get FBA max container capacity",
               response_model=BasicResponse[dict])
def get_fba_max_ctn_capacity(sku: str):
    with FbaService() as fba_svc:
        max_capacity = fba_svc.get_fba_max_ctn_capacity(sku)
    return ResponseSuccess(data=max_capacity)