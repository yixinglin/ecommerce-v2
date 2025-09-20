import datetime
import hashlib
import os
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from core.config2 import settings
from core.log import logger
from models import PrintTaskModel, PrintLogModel
from models.print_task import PrintTask_Pydantic, PrintStatus, PrintLog_Pydantic, PrintFileModel, PrintFile_Pydantic
from utils import utilpdf

UPLOAD_DIR = settings.static.upload_dir

class PrintTaskService:
    def __init__(self):
        pass

    async def create_print_log(self, task_id: int, content: str):
        content = content.strip()[:200]
        task_obj = await PrintLogModel.create(
            task_id=task_id,
            content=content,
        )
        new_log = await PrintLog_Pydantic.from_tortoise_orm(task_obj)
        return new_log

    async def create_print_task(self, task_name: str, created_by: str,
                          file_paths: List[str], **kwargs):
        # 组合多个文件路径（使用分号分隔）
        if isinstance(file_paths, list):
            file_paths = ";".join(file_paths)
        else:
            file_paths = ""

        # 创建数据库记录
        task_obj = await PrintTaskModel.create(
            task_name=task_name,
            created_by=created_by,
            file_paths=file_paths
        )
        new_task = await PrintTask_Pydantic.from_tortoise_orm(task_obj)
        new_log = await self.create_print_log(new_task.id,
                                         f"Task created by {created_by}")
        return new_task

    async def get_print_task_by_id(self, task_id: int):
        try:
            task_obj = await PrintTaskModel.get(id=task_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Task not found")
        return await PrintTask_Pydantic.from_tortoise_orm(task_obj)

    async def get_print_tasks(self, offset, limit, keyword, **kwargs):
        query = Q()
        if keyword:
            query &= Q(task_name__icontains=keyword)
        qs = PrintTaskModel.filter(query, **kwargs)
        total = await qs.count()
        tasks = qs.order_by("-id").offset(offset).limit(limit)
        ans = await PrintTask_Pydantic.from_queryset(tasks)
        return {
            "total": total,
            "data": ans
        }

    async def update_print_task(self, task_id: int,
                                task_name: str,
                                created_by: str,
                                printed_by: str, status: str,
                                file_paths: List[str],
                                skip: int,
                                signature: str,
                                **kwargs):
        task_obj = await PrintTaskModel.get_or_none(id=task_id)
        if not task_obj:
            raise HTTPException(status_code=404, detail="Task not found")

        if task_name is not None and task_obj.task_name != task_name:
            task_obj.task_name = task_name
            new_log = await self.create_print_log(task_id, f"Task name updated to {task_name}")
        if printed_by is not None and task_obj.printed_by != printed_by:
            task_obj.printed_by = printed_by
            new_log = await self.create_print_log(task_id, f"Task will be printed by {printed_by}")
        if created_by is not None and task_obj.created_by != created_by:
            task_obj.created_by = created_by
            new_log = await self.create_print_log(task_id, f"Task created by {created_by}")
        if status is not None and task_obj.status != status:
            task_obj.status = status
            if status == PrintStatus.PRINTED:
                task_obj.printed_at = datetime.datetime.utcnow()
                new_log = await self.create_print_log(task_id, f"Task updated to finished")
            elif status == PrintStatus.PRINTING:
                new_log = await self.create_print_log(task_id, f"Task updated to printing by {printed_by}")
            elif status == PrintStatus.CANCELLED:
                new_log = await self.create_print_log(task_id, f"Task updated to cancelled")
            elif status == PrintStatus.NOT_PRINTED:
                task_obj.printed_at = None
                new_log = await self.create_print_log(task_id, f"Task updated to pending")
        if skip is not None and task_obj.skip != skip:
            task_obj.skip = skip
            new_log = await self.create_print_log(task_id, f"Task skip updated to {skip}")
        if isinstance(file_paths, list):
            file_paths_ = ";".join(file_paths)
            if task_obj.file_paths != file_paths_:
                task_obj.file_paths = file_paths_
                new_log = await self.create_print_log(task_id, f"Task file paths updated to {file_paths_}")

        await task_obj.save()
        return await PrintTask_Pydantic.from_tortoise_orm(task_obj)

    async def query_print_logs(self, task_id: int):
        try:
            # sort by date desc
            task_obj = await PrintTaskModel.get(id=task_id)
            logs = task_obj.logs.all().order_by("-created_at")
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Task not found")
        logs_pydantic = await PrintLog_Pydantic.from_queryset(logs)
        return logs_pydantic



class PrintFileAddRequest(BaseModel):
    file_name: str
    file_path: str

class PrintFileUpdateRequest(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    archived: Optional[bool] = None
    print_count: Optional[int] = None

class PrintFileService:

    def __init__(self):
        pass

    async def get_print_file_by_id(self, id: int):
        try:
            print_file = await PrintFileModel.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="File not found")
        return print_file


    async def get_print_files(self, offset, limit, keyword, **kwargs):
        query = Q()
        if keyword:
            query &= Q(file_name__icontains=keyword)
            query |= Q(description__icontains=keyword)
        qs = PrintFileModel.filter(query, **kwargs)
        total = await qs.count()
        files = qs.order_by("-id").offset(offset).limit(limit)
        ans = await PrintFile_Pydantic.from_queryset(files)
        return {
            "total": total,
            "data": ans
        }

    def __bytes_to_hash(self, content: bytes) -> str:
        md5_hash = hashlib.md5(content).hexdigest()
        return md5_hash

    async def add_print_file(self, body: PrintFileAddRequest):
        logger.info(f"add_print_file: {body}")
        file_path = UPLOAD_DIR + body.file_path
        file_name = body.file_name
        file_type = "application/pdf"
        now_ = datetime.datetime.now()

        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="File not found")

        with open(file_path, "rb") as f:
            content = f.read()

        # Check if file is a PDF
        if not utilpdf.is_pdf(content):
            raise HTTPException(status_code=400, detail="File is not a PDF")

        if not content:
            raise HTTPException(status_code=400, detail="File content is empty")
        else:
            md5_hash = self.__bytes_to_hash(content)
            total_pages = utilpdf.count_pages(content)

        if total_pages < 1:
            raise HTTPException(status_code=400, detail="File has no pages")

        # Check if file already exists
        print_file = await PrintFileModel.filter(file_hash=md5_hash).first()
        if print_file:
            await PrintFileModel.filter(file_hash=md5_hash).update(
                **body.dict(exclude_unset=True),
                updated_at=now_
            )
            logger.info(f"File already exists: id={print_file.id}")
            logger.info(f"File updated: body={body.dict(exclude_unset=True)}")
            return await PrintFileModel.get(id=print_file.id)

        # Add file to database
        print_file = await PrintFileModel.create(
            file_name=file_name,
            file_path=file_path,
            file_hash=md5_hash,
            file_size=len(content),
            file_pages=total_pages,
            file_type=file_type,
            file_extension=file_path.split(".")[-1],
            created_by="system",
        )
        logger.info(f"File added: {print_file.id}, file_name: {file_name}, file_path: {file_path}")
        return await PrintFileModel.get(id=print_file.id)


    async def add_print_files(self, body: List[PrintFileAddRequest]):
        count = 0
        result_list = []
        try:
            async with in_transaction():
                for file in body:
                    result = await self.add_print_file(file)
                    result_list.append(result)
                    count += 1
        except Exception as e:
            logger.error(f"Error adding print files: {e}")
            raise HTTPException(status_code=500, detail="Error adding print files")

        result_list = [await PrintFile_Pydantic.from_tortoise_orm(r) for r in result_list]
        return {
            "data": result_list,
            "total": count
        }

    async def update_print_file(self, id: int, body: PrintFileUpdateRequest):
        logger.info(f"update_print_file: {id}, {body}")
        print_file = await PrintFileModel.filter(id=id).first()
        if not print_file:
            raise HTTPException(status_code=404, detail="File not found")

        await PrintFileModel.filter(id=id).update(
            **body.dict(exclude_unset=True),
            updated_at=datetime.datetime.now()
        )
        logger.info(f"File updated: id={id}")
        return await PrintFileModel.get(id=id)

    async def delete_print_file(self, id: int):
        logger.info(f"delete print file: {id}")
        print_file = await PrintFileModel.filter(id=id).first()
        if not print_file:
            raise HTTPException(status_code=404, detail="File not found")

        count = await PrintFileModel.filter(id=id).delete()
        return {
            "count": count,
            "file_name": print_file.file_name,
            "file_path": print_file.file_path,
        }










