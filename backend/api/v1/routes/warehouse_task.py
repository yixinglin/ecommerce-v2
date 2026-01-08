from typing import List, Dict

from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException
from app.warehouse_tasks.models import WarehouseTaskModel_Pydantic, WarehouseTaskActionLog_Pydantic
from app.warehouse_tasks.schemas import WarehouseTaskPayload, TaskQuery, TaskActionPayload, TaskActionLogQuery
from app.warehouse_tasks.services import WarehouseTaskService, TaskActionLogService
from core.log import logger
from core.response import ListResponse
from core.response2 import BaseResponse, Page

wtm_router = APIRouter(prefix="/tasks")
action_log_router = APIRouter(prefix="/action_logs")

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
    response_model=BaseResponse[WarehouseTaskModel_Pydantic]
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
    response_model=BaseResponse[WarehouseTaskModel_Pydantic]
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
    response_model=BaseResponse[Page[WarehouseTaskModel_Pydantic]]
)
async def list_tasks(
    query: TaskQuery,
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

@wtm_router.put(
        "/{task_id}/reset",
        response_model=BaseResponse[Page[WarehouseTaskActionLog_Pydantic]]
)
async def reset_task(
        task_id: int,
        service: WarehouseTaskService = Depends(get_service)
):
    task = await service.reset_task(task_id)
    return task


@wtm_router.post(
    "/{task_id}/perform-action",
    response_model=BaseResponse[WarehouseTaskModel_Pydantic]
)
async def perform_action(
        task_id: int,
        request: TaskActionPayload,
        service: WarehouseTaskService = Depends(get_service)
):
    try:
        resp = await service.perform_action(task_id, request)
    except ValueError as e:
        logger.error(f"Error performing action: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing action: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return BaseResponse.success(data=resp)


def get_action_log_service() -> TaskActionLogService:
    return TaskActionLogService()

@action_log_router.post(
    "/list",
    response_model=BaseResponse[Page[WarehouseTaskActionLog_Pydantic]]
)
async def list_action_logs(
        query: TaskActionLogQuery,
        service: TaskActionLogService = Depends(get_action_log_service)
):
    try:
        items = await service.list_logs(query=query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing action logs: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return items

@action_log_router.get(
    "/available_actions/{task_id}",
    response_model=BaseResponse[List[Dict]]
)
async def get_available_actions(
        task_id: int,
        service: TaskActionLogService = Depends(get_action_log_service)
):
    try:
        actions = await service.get_available_actions(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting available actions: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return BaseResponse(data=actions)