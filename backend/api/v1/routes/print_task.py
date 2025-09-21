import datetime
from typing import List, Dict, Optional
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException
from starlette.responses import Response
from utils import utilpdf
from models.print_task import PrintTask_Pydantic, PrintStatus, PrintLog_Pydantic, PrintFile_Pydantic
from schemas.print_task import PrintFileAddRequest, PrintFileUpdateRequest
from services.printshop.print_task import PrintTaskService, PrintFileService


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
async def get_print_tasks(
    offset: int = 0,
    limit: int = 10,
    keyword: Optional[str] = None,
):
    service = PrintTaskService()
    tasks = await service.get_print_tasks(
        offset=offset,
        limit=limit,
        keyword=keyword
    )
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
        skip: int = Form(None),
        signature: str = Form(None)):
    services = PrintTaskService()
    task_obj = await services.update_print_task(task_id=task_id,
                               task_name=task_name,
                               created_by=created_by,
                               printed_by=printed_by,
                               status=status,
                               file_paths=file_paths,
                               skip=skip,
                               signature=signature)
    return task_obj

@print_task_router.get("/log/query/{task_id}",
                         response_model=List[PrintLog_Pydantic])
async def query_print_logs(task_id: int):
    services = PrintTaskService()
    logs = await services.query_print_logs(task_id)
    return logs


# --------------- Print File ---------------------
print_file_router = APIRouter()

@print_file_router.post(
    "/file/create",
    response_model=PrintFile_Pydantic,
)
async def add_print_file(file: PrintFileAddRequest):
    service = PrintFileService()
    new_file = await service.add_print_file(file)
    return new_file

@print_file_router.post(
    "/file/create/bulk",
    response_model=Dict,
)
async def add_print_files(body: List[PrintFileAddRequest]):
    service = PrintFileService()
    results = await service.add_print_files(body)
    return results



@print_file_router.get(
    "/file/print/{file_id}",
    response_class=Response,
)
async def request_printing(file_id: int, copies: int = 1):
    service = PrintFileService()
    if copies > 1024:
        raise HTTPException(status_code=400, detail="Copies should be less than 1024")

    results = await service.request_printing(file_id, copies)
    file = results.get("file")
    pdf = results.get("pdf")
    if not file or not pdf:
        raise HTTPException(status_code=400, detail="Failed to print file")
    file_name = quote(file.file_name)
    pdf_bytes = utilpdf.str_to_pdf(pdf)
    inline = True
    if inline:
        disposition = f"inline; filename={file_name}.pdf"
    else:
        disposition = f"attachment; filename={file_name}.pdf"

    headers = {
        "Content-Disposition": disposition,
        "Content-Length": str(len(pdf_bytes))
    }

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers
    )


@print_file_router.put(
    "/file/update/{file_id}",
    response_model=PrintFile_Pydantic,
)
async def update_print_file(file_id: int, file: PrintFileUpdateRequest):
    service = PrintFileService()
    updated_file = await service.update_print_file(file_id, file)
    return updated_file

@print_file_router.get(
    "/file/query/{file_id}",
    response_model=PrintFile_Pydantic
)
async def get_print_file(file_id: int):
    service = PrintFileService()
    file = await service.get_print_file_by_id(file_id)
    return file

@print_file_router.get(
    "/file/query",
    response_model=Dict,
)
async def get_print_files(
    offset: int = 0,
    limit: int = 10,
    keyword: Optional[str] = None,
    include_archived: Optional[bool] = False,
):
    service = PrintFileService()
    results = await service.get_print_files(
        offset=offset,
        limit=limit,
        keyword=keyword,
        include_archived=include_archived
    )
    return results


@print_file_router.delete(
    "/file/delete/{file_id}",
    response_model=Dict,
)
async def delete_print_file(file_id: int):
    service = PrintFileService()
    results = await service.delete_print_file(file_id)
    return results
