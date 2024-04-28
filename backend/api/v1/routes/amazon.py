import os
from typing import Any, List
from fastapi import APIRouter, Request, Response
from schemas import ResponseSuccess
from rest import AmazonOrderMongoDBManager, AmazonCatalogManager
from core.config import settings
from vo.amazon import DailyShipment, DailySalesCountVO
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

amz_order = APIRouter(tags=['AMAZON API'])


def get_asin_image_url_dict() -> dict:
    with AmazonCatalogManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        catalogItems = man.get_all_catalog_items()
    result = dict()
    for catalogItem in catalogItems:
        result[catalogItem['_id']] = catalogItem['catalogItem']['AttributeSets'][0]['SmallImage']['URL']
    return result


@amz_order.get("/orders/ordered-items-count/daily/{days_ago}",
               summary="Get daily ordered items count",
               response_model=ResponseSuccess[List[DailySalesCountVO]])
def get_daily_ordered_items_count(response: Response, days_ago: int = 7) -> Any:
    with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
        daily = man.get_daily_mfn_sales(days_ago=days_ago)

    # Convert daily-sales data to DailySalesCountVO objects
    daily_sales_vo = []
    for day in daily:
        # Convert dailyShipments JSON array to list of DailyShipment objects
        daily_shipments = [DailyShipment(**item) for item in day['dailyShipments']]
        # Create DailySalesCountVO object
        vo = DailySalesCountVO(purchaseDate=day['purchaseDate'],
                               hasUnshippedOrderItems=day['dailyShippedItemsCount'] < day['dailyOrdersItemsCount'],
                               dailyShippedItemsCount=day['dailyShippedItemsCount'],
                               dailyOrdersItemsCount=day['dailyOrdersItemsCount'],
                               dailyShipments=daily_shipments)
        daily_sales_vo.append(vo)

    asin_image_url = get_asin_image_url_dict()
    for day in daily_sales_vo:
        for shipment in day.dailyShipments:
            shipment.imageUrl = asin_image_url[shipment.asin]
    return ResponseSuccess(data=daily_sales_vo, )


# Show daily ordered items count using html template
@amz_order.get("/orders/ordered-items-count/daily/{days_ago}/treeview",
               summary="Get daily ordered items count in html format",
               response_class=HTMLResponse)
def view_daily_ordered_items_count_html(days_ago: int, request: Request, response: Response, ) -> Any:
    data = get_daily_ordered_items_count(days_ago=days_ago, response=response)
    templates = Jinja2Templates(directory=os.path.join("assets", "templates", "web"))
    response.headers["Cache-Control"] = "max-age=3600"
    # response.headers["xtoken"] = "asdasdasdas"
    return templates.TemplateResponse(name="DailySalesCount.html",
                                      request=request,
                                      headers={"Cache-Control": "max-age=3600, public"},
                                      context={"data": data.data})
