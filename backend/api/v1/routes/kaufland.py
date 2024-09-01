import os
from typing import Any, List

from fastapi import APIRouter, Response, Request
from fastapi.responses import HTMLResponse
from services.kaufland.KauflandOrderService import KauflandOrderSerice
from fastapi.templating import Jinja2Templates

from schemas import BasicResponse, ResponseSuccess
from schemas.kaufland import DailySalesCountVO, Product

kfld_order = APIRouter()


@kfld_order.get("/orders/ordered-items-count/daily/{days_ago}",
               summary="Get daily ordered items count",
                response_model=BasicResponse[List[DailySalesCountVO]])
def get_daily_ordered_items_count(response: Response, days_ago: int = 7) -> Any:
    with KauflandOrderSerice(key_index=0) as man:
        daily = man.get_daily_sales(days_ago=days_ago)
    daily_sales_count_vo = []
    # convert to vo
    for day in daily:
        products = [Product(**item) for item in day['products']]
        vo = DailySalesCountVO(createdDate=day['date'],
                               status=day['status'],
                               products=products)
        daily_sales_count_vo.append(vo)
    # filter all cancelled orders
    daily_sales_count_vo = list(filter(lambda x: x.status != 'cancelled', daily_sales_count_vo, ))
    resp = ResponseSuccess(data=daily_sales_count_vo)
    return resp


@kfld_order.get("/orders/ordered-items-count/daily/{days_ago}/view",
               summary="Get daily ordered items count",
                response_class=HTMLResponse)
def get_daily_ordered_items_count_html(days_ago: int, request: Request, response: Response):
    data = get_daily_ordered_items_count(days_ago=days_ago, response=response)
    templates = Jinja2Templates(directory=os.path.join("assets", "templates", "web"))
    response.headers["Cache-Control"] = "max-age=3600"
    return templates.TemplateResponse(name="KauflandDailySalesCount.html",
                                      request=request,
                                      headers={"Cache-Control": "max-age=3600, public"},
                                      context={"data": data.data})
