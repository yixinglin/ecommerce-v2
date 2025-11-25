from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist

from app import OrderBatchModel_Pydantic, OrderErrorLogModel_Pydantic, OrderStatusLogModel_Pydantic, \
    ShippingLabelModel_Pydantic, AddressModel_Pydantic
from app.order_fulfillment.common.enums import (
    IntegrationType, OrderStatus, OrderBatchStatus, AddressType, ChannelCode, OperationType, CarrierCode
)
from app.order_fulfillment.common.exceptions import TrackingInfoSyncError
from app.order_fulfillment.models import ShippingTrackingModel_Pydantic
from app.order_fulfillment.schemas import OrderQueryRequest, OrderResponse, OrderUpdateRequest, PullOrdersRequest, \
    CreateBatchRequest, IntegrationCredentialResponse, IntegrationCredentialUpdateRequest, OrderItemResponse, \
    AddressUpdateRequest, ShippingTrackingResponse
from app.order_fulfillment.services import OrderService, ShippingLabelService, BatchService, CredentialService, \
    ShippingTrackingService
from core.log import logger
from core.response import ListResponse

ofa_router = APIRouter()

@ofa_router.get("/enums")
def get_all_enums():
    return {
        "channel_codes": [{"value": e.value, "label": e.name.title()} for e in ChannelCode],
        "order_status": [{"value": e.value, "label": e.name.title()} for e in OrderStatus],
        "address_type": [{"value": e.value, "label": e.name.title()} for e in AddressType],
        "carrier_code": [{"value": e.value, "label": e.name.upper()} for e in CarrierCode],
        "operation_type": [{"value": e.value, "label": e.name.title()} for e in OperationType],
        "integration_type": [{"value": e.value, "label": e.name.title()} for e in IntegrationType],
        "order_batch_status": [{"value": e.value, "label": e.name.title()} for e in OrderBatchStatus],
    }


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


class GenerateLabelRequest(BaseModel):
    external_logistic_id: str
    more_labels: Optional[bool] = False

@ofa_router.post(
    "/orders/{order_id}/generate_label",
    summary="Generate shipping label for order",
)
async def generate_labels(
        order_id: int,
        payload: GenerateLabelRequest,
) -> dict:
    service = ShippingLabelService()
    try:
        if not payload.more_labels:
            success = await service.generate_label(
                order_id,
                payload.external_logistic_id
            )
        else:
            success = await service.generate_further_label(
                order_id,
                payload.external_logistic_id,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating label for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": success}

@ofa_router.post(
    "/orders/{order_id}/tracking_status",
    summary="Update shipping tracking status for order",
)
async def update_shipping_tracking_status(order_id: int, external_logistic_id: str) -> ShippingTrackingResponse:
    try:
        track = await ShippingTrackingService.update_tracking_status(order_id, external_logistic_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating shipping tracking status for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return track

@ofa_router.get(
    "/orders/{order_id}/tracking_status",
    response_model=ShippingTrackingModel_Pydantic,
    summary="Get shipping tracking status for order",
)
async def get_shipping_tracking_status(order_id: int) -> ShippingTrackingModel_Pydantic:
    try:
        track = await ShippingTrackingService.get_tracking_status(order_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting shipping tracking status for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return track

@ofa_router.get("/orders/{order_id}/labels")
async def get_labels(order_id: int) -> ListResponse[ShippingLabelModel_Pydantic]:
    try:
        labels = await ShippingLabelService.get_labels(order_id)
    except Exception as e:
        logger.error(f"Error getting labels for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return labels

@ofa_router.get(
    "/orders/{order_id}/labels/pdf",
    response_class=Response,
    summary="Get shipping labels"
)
async def get_labels_pdf(order_id: int) -> Response:
    try:
        buff = await ShippingLabelService.get_labels_pdf(order_id)
        bytes_ = buff.read()
        filename = f"parcel_label_{order_id}.pdf"
        disposition = f'attachment; filename="{filename}"'
        headers = {
            "Content-Disposition": disposition,
            "Content-Length": str(len(bytes_))
        }
        response = Response(
            content=bytes_,
            media_type="application/pdf",
            headers=headers
        )
        return response
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting labels pdf for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@ofa_router.get("/orders/{order_id}/address/{address_type}")
async def get_address_from_order(order_id: int, address_type: AddressType) -> AddressModel_Pydantic:
    try:
        address = await OrderService.get_address(order_id, address_type)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"Address for order {order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting address for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return address

@ofa_router.put("/orders/{order_id}/address/{address_type}")
async def update_shipping_address_in_order(
    order_id: int,
    address: AddressUpdateRequest,
    address_type: AddressType=AddressType.SHIPPING,
) -> AddressModel_Pydantic:
    try:
        updated_address = await OrderService.update_address(
            order_id=order_id,
            address_type=address_type,
            update_request=address
        )
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"Address for order {order_id} not found: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating address for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return updated_address

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

@ofa_router.get(
    "/orders/{order_id}/zip",
    summary="Get order documents as a zip file",
    response_class=Response
)
async def get_order_documents(order_id: int) -> Response:
    try:
        buff = await OrderService.get_order_documents(order_id)
        bytes_ = buff.read()
        filename = f"documents_{order_id}.zip"
        disposition = f'attachment; filename="{filename}"'
        headers = {
            "Content-Disposition": disposition,
            "Content-Length": str(len(bytes_))
        }
        response = Response(
            content=bytes_,
            media_type="application/zip",
            headers=headers
        )

        return response
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting order documents for order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@ofa_router.delete("/orders/{order_id}")
async def delete_order(order_id: int):
    try:
        await OrderService.delete_order(order_id)
    except DoesNotExist as e:
        raise HTTPException(status_code=404, detail=f"{order_id} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True}


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
    response_class=Response
)
async def download_batch(batch_id: str) -> Response:
    try:
        zip_file = await BatchService.download_batch_zip(batch_id)
        filename = f"{batch_id}.zip"
        disposition = f'attachment; filename="{filename}"'
        headers = {
            "Content-Disposition": disposition,
            "Content-Length": str(len(zip_file))
        }
        return Response(
            content=zip_file,
            media_type="application/zip",
            headers=headers
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
