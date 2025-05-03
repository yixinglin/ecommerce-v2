from typing import List, Dict
from fastapi import APIRouter, Form, File, UploadFile
from models.print_task import PrintTask_Pydantic, PrintStatus, PrintLog_Pydantic
from services.printshop.print_task import PrintTaskService

print_task_router = APIRouter()

@print_task_router.post("/task/create", response_model=PrintTask_Pydantic)
async def create_print_task(
        task_name: str = Form(...),
        created_by: str = Form(...),
        file_paths: List[str] = Form(None)  # 支持多文件上传
):
    service = PrintTaskService()
    new_task = await service.create_print_task(task_name, created_by, file_paths)
    return new_task


@print_task_router.get("/task/query/{task_id}", response_model=PrintTask_Pydantic)
async def get_print_task(task_id: int):
    service = PrintTaskService()
    task = await service.get_print_task_by_id(task_id)
    return task

@print_task_router.get("/task/query", response_model=Dict)
async def get_print_tasks(offset: int = 0, limit: int = 10):
    service = PrintTaskService()
    tasks = await service.get_print_tasks(offset, limit)
    return tasks

@print_task_router.put("/task/update/{task_id}",
                       response_model=PrintTask_Pydantic)
async def update_print_task(
        task_id: int,
        task_name: str = Form(None),
        printed_by: str = Form(None),
        created_by: str = Form(None),
        status: PrintStatus = Form(PrintStatus.NOT_PRINTED),
        file_paths: List[str] = Form(None),  # 支持多文件上传
        signature: str = Form(None)):
    services = PrintTaskService()
    task_obj = await services.update_print_task(task_id=task_id,
                               task_name=task_name,
                               created_by=created_by,
                               printed_by=printed_by,
                               status=status,
                               file_paths=file_paths,
                               signature=signature)
    return task_obj

@print_task_router.get("/log/query/{task_id}",
                         response_model=List[PrintLog_Pydantic])
async def query_print_logs(task_id: int):
    services = PrintTaskService()
    logs = await services.query_print_logs(task_id)
    return logs