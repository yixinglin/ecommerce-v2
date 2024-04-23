import os
from typing import Any, List
from fastapi import APIRouter, Request
from schemas import ResponseSuccess
from rest import AmazonOrderMongoDBManager
from core.config import settings
from vo.amazon import DailyShipment, DailySalesCountVO
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

amz_order = APIRouter()


@amz_order.get("/orders/ordered-items-count/daily/{days_ago}",
               summary="Get daily ordered items count",
               response_model=ResponseSuccess[List[DailySalesCountVO]])
async def get_daily_ordered_items_count(days_ago: int = 7) -> Any:
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
    return ResponseSuccess(data=daily_sales_vo, )


# Show daily ordered items count using html template
@amz_order.get("/orders/ordered-items-count/daily/{days_ago}/treeview",
               summary="Get daily ordered items count in html format",
               response_class=HTMLResponse)
async def view_daily_ordered_items_count_html(days_ago: int, request: Request) -> Any:
    response = await get_daily_ordered_items_count(days_ago=days_ago)
    templates = Jinja2Templates(directory=os.path.join("assets", "templates", "web"))
    return templates.TemplateResponse(name="DailySalesCount.html",
                                      request=request,
                                      context={"data": response.data})
