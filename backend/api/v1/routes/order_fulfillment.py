import io

from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException
from starlette.responses import StreamingResponse
from tortoise.exceptions import DoesNotExist

from app import OrderBatchModel_Pydantic, OrderErrorLogModel_Pydantic, OrderStatusLogModel_Pydantic, \
    OrderItemModel_Pydantic
from app.order_fulfillment.common.exceptions import TrackingInfoSyncError
from app.order_fulfillment.schemas import OrderQueryRequest, OrderResponse, OrderUpdateRequest, PullOrdersRequest, \
    CreateBatchRequest, IntegrationCredentialResponse, IntegrationCredentialUpdateRequest, OrderItemResponse
from app.order_fulfillment.services import OrderService, LabelService, BatchService, CredentialService
from core.log import logger
from core.response import ListResponse

ofa_router = APIRouter()


@ofa_router.post(
    "/orders/pull",
    summary="Pull orders from specified channel and save them to database",
)
async def pull_orders(payload: PullOrdersRequest) -> dict[str, int]:
    try:
        service = OrderService(**payload.dict())
        await service.init_credentials()
        count = await service.pull_orders()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error pulling orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"success_count": count}


@ofa_router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
)
async def get_order(order_id: int) -> OrderResponse:
    try:
        order = await OrderService.get_order(order_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found")
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return order


@ofa_router.get(
    "/orders",
    response_model=ListResponse[OrderResponse],
    summary="List orders from database",
)
async def list_orders(query: OrderQueryRequest = Depends(), ):
    try:
        results = await OrderService.list_orders(query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return results


# /generate_labels
@ofa_router.post(
    "/orders/{order_id}/generate_label",
    summary="Generate shipping label for order",
)
async def generate_labels(
        order_id: int,
        external_logistic_id: str
) -> dict:
    service = LabelService()
    try:
        success = await service.generate_label(
            order_id,
            external_logistic_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating label for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": success}


@ofa_router.put(
    "/orders/{order_id}/update",
    summary="Update order",
)
async def update_order(order_id: int, update: OrderUpdateRequest) -> OrderResponse:
    try:
        order = await OrderService.update_order(order_id, update)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return order

@ofa_router.get("/orders/{order_id}/items")
async def get_order_items(order_id: int) -> ListResponse[OrderItemResponse]:
    try:
        items = await OrderService.get_order_items(order_id)
    except Exception as e:
        logger.error(f"Error getting order items for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return items

@ofa_router.post(
    "/orders/{order_id}/sync_tracking",
    summary="Sync tracking info for order",
)
async def sync_tracking_info(order_id: int) -> dict:
    try:
        success = await OrderService.sync_tracking_info(order_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except TrackingInfoSyncError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing tracking info for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": success}

@ofa_router.get("/orders/{order_id}/errors")
async def get_order_errors(order_id: int) -> ListResponse[OrderErrorLogModel_Pydantic]:
    try:
        errors = await OrderService.get_order_errors(order_id)
    except Exception as e:
        logger.error(f"Error getting order errors for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return errors

@ofa_router.get("/orders/{order_id}/status_logs")
async def get_order_status_logs(order_id: int) -> ListResponse[OrderStatusLogModel_Pydantic]:
    try:
        logs = await OrderService.get_order_status_logs(order_id)
    except Exception as e:
        logger.error(f"Error getting order status logs for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return logs


@ofa_router.post("/batches/create")
async def create_batch(payload: CreateBatchRequest) -> dict:
    try:
        batch_id = await BatchService.generate_batch_from_synced_orders(
            channel=payload.channel_code,
            account_id=payload.account_id,
            operator=payload.operator
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    if not batch_id:
        raise HTTPException(status_code=400, detail="No synced orders found")

    return {"batch_id": batch_id}


@ofa_router.get("/batches")
async def list_batches(page: int = 1, limit: int = 10) -> ListResponse[OrderBatchModel_Pydantic]:
    try:
        results = await BatchService.list_batches(page, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing batches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return results


@ofa_router.get(
    "/batches/{batch_id}/download",
    summary="Download batch as a zip file",
    response_class=StreamingResponse
)
async def download_batch(batch_id: str) -> StreamingResponse:
    try:
        zip_file = await BatchService.download_batch_zip(batch_id)
        buffer = io.BytesIO(zip_file)
        filename = f"{batch_id}.zip"
        return StreamingResponse(
            buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{batch_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error downloading batch {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ofa_router.post("/batches/{batch_id}/complete")
async def complete_batch(batch_id: str):
    try:
        await BatchService.complete_batch(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{batch_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error completing batch {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True}


@ofa_router.get("/credentials")
async def list_credentials(page: int = 1, limit: int = 10) -> ListResponse[IntegrationCredentialResponse]:
    try:
        credentials = await CredentialService.list_credentials(
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return credentials

@ofa_router.put("/credentials/{credential_id}/update")
async def update_credential(credential_id: int, update: IntegrationCredentialUpdateRequest):
    try:
        credential = await CredentialService.update_credential(
            credential_id=credential_id,
            update_request=update
        )
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{credential_id} not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating credential {credential_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return credential
