import os
from typing import Any

from fastapi import APIRouter, Response, Request
from fastapi.responses import HTMLResponse
from core.config import settings
from rest.kaufland.DataManager import KauflandOrderMongoDBManager
from fastapi.templating import Jinja2Templates

from schemas import ResponseSuccess

kfld_order = APIRouter(tags=['Kaufland API'])


@kfld_order.get("/orders/ordered-items-count/daily/{days_ago}",
               summary="Get daily ordered items count")
def get_daily_ordered_items_count(response: Response, days_ago: int=7) -> Any:
    with KauflandOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT, settings.DB_MONGO_PORT) as man:
        daily = man.get_daily_sales(days_ago=days_ago)
    resp = ResponseSuccess(data=daily)
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
