import io
from typing import TypeVar, Generic, List

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from core.config2 import settings
from models.woocommerce import OrderModel, OrderStatus
from schemas import BasicResponse
from services.woocommerce.woocommerce import OrderService as WooOrderService

order_router = APIRouter(prefix="/orders")

key_index = settings.api_keys.wp_access_key_index

T = TypeVar('T')

class ListResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    offset: int
    limit: int


@order_router.get(
    "/{order_id}",
    summary="Get order by id",
    response_model=BasicResponse[dict],
)
async def get_order(order_id: int):
    pass



OrderListResponse = ListResponse[OrderModel]

@order_router.get(
    "/",
    summary="Get order list",
    response_model=OrderListResponse,
)
async def get_order_list(
        status: OrderStatus = None,
        limit: int = 10,
        offset: int = 0
):
    # No need to use api key.
    async with WooOrderService(key_index=None) as service:
        results = await service.find_orders(
            limit=limit,
            offset=offset,
            status=status.value if status else None,
        )
        return OrderListResponse(
            data=results['data'],
            total=results['total'],
            offset=offset,
            limit=limit,
        )
@order_router.get(
    "/stat/ordered_sku",
    summary="Get ordered sku statistics",
    response_class=StreamingResponse,)
async def get_ordered_sku_statistcs(days_ago:int=7):
    # xlsx as response
    async with WooOrderService(key_index=None) as service:
        df_results = await service.stat_ordered_sku(days_ago=days_ago)
        buffer = io.BytesIO()
        df_results.to_excel(buffer, index=False)
        buffer.seek(0)
        headers = {
            'Content-Disposition': 'attachment; filename="statistics_ordered_sku.xlsx"'
        }
        return StreamingResponse(
            buffer,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )