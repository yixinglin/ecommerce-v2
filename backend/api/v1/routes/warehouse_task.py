

from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException

from app.warehouse_tasks.models import WarehouseTaskModel_Pydantic
from app.warehouse_tasks.schemas import WarehouseTaskPayload, TaskQueryRequest
from app.warehouse_tasks.services import WarehouseTaskService
from core.log import logger
from core.response import ListResponse

wtm_router = APIRouter(prefix="/tasks")

def get_service() -> WarehouseTaskService:
    return WarehouseTaskService()


@wtm_router.post(
    "/create",
    response_model=WarehouseTaskModel_Pydantic
)
async def create_task(
    data: WarehouseTaskPayload,
    service: WarehouseTaskService = Depends(get_service)
):
    task = await service.create_task(data)
    return task


@wtm_router.put(
    "/update/{task_id}",
    response_model=WarehouseTaskModel_Pydantic
)
async def update_task(
    task_id: int,
    data: WarehouseTaskPayload,
    service: WarehouseTaskService = Depends(get_service)
):
    task = await service.update_task(task_id, data)
    return task

@wtm_router.get(
    "/{task_id}",
    response_model=WarehouseTaskModel_Pydantic
)
async def get_task(
    task_id: int,
    service: WarehouseTaskService = Depends(get_service)
):
    try:
        task = await service.get_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return task

@wtm_router.post(
    "/list",
    response_model=ListResponse[WarehouseTaskModel_Pydantic]
)
async def list_tasks(
    query: TaskQueryRequest,
    service: WarehouseTaskService = Depends(get_service)
):
    try:
        resp = await service.list_tasks(request=query)
        pass
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return resp


@wtm_router.delete(
    "/{task_id}"
)
async def delete_task(
    task_id: int,
    service: WarehouseTaskService = Depends(get_service)
):
    await service.delete_task(task_id)
    return {"success": True}