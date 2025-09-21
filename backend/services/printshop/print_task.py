import asyncio
import datetime
import hashlib
import os
from typing import List

from fastapi import HTTPException
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from core.config2 import settings
from core.log import logger
from models import PrintTaskModel, PrintLogModel
from models.print_task import PrintTask_Pydantic, PrintStatus, PrintLog_Pydantic, PrintFileModel, PrintFile_Pydantic
from schemas.print_task import PrintFileAddRequest, PrintFileUpdateRequest
from utils import utilpdf
import utils.time as time_utils

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

class PrintFileService:

    def __init__(self):
        pass

    async def get_print_file_by_id(self, id: int):
        try:
            print_file = await PrintFileModel.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="File not found")
        return print_file


    async def get_print_files(
            self, offset, limit,
            keyword,
            include_archived=False,
            **kwargs
    ):
        query = Q()
        if keyword:
            query &= Q(file_name__icontains=keyword) | Q(description__icontains=keyword)
        if not include_archived:
            query &= Q(archived=False)
        qs = PrintFileModel.filter(query, **kwargs)
        total = await qs.count()
        files = qs.order_by("-id").offset(offset).limit(limit)
        ans = await PrintFile_Pydantic.from_queryset(files)
        return {
            "total": total,
            "data": ans
        }

    async def request_printing(self, id: int, copies: int):
        pr_file = await self.get_print_file_by_id(id)
        if not pr_file:
            raise HTTPException(status_code=404, detail="Print file not found")
        if pr_file.archived:
            raise HTTPException(status_code=400, detail="Print file is archived")
        # Copy file
        file_path = UPLOAD_DIR + pr_file.file_path
        with open(file_path, "rb") as fp:
            pdf_bytes = fp.read()

        if not utilpdf.is_pdf(pdf_bytes):
            raise HTTPException(status_code=400, detail="Non-PDF file is not allowed")

        total_pages = utilpdf.count_pages(pdf_bytes)
        if copies > 1 and total_pages > 1:
            raise HTTPException(
                status_code=400,
                detail="PDF files with more than one page cannot be copied"
            )

        try:
            w, h = utilpdf.extract_pdf_size(pdf_bytes)
            # Add file name
            pattern = "%Y-%m-%d_%H:%M"
            watermark_text = f"{pr_file.file_name} | {time_utils.now(pattern)} | <{pr_file.file_hash[:5]}>"
            watermark_bytes = await self.__add_watermark_to_pdf(pdf_bytes=pdf_bytes,
                                        watermark_text=watermark_text,
                                        font_size=8,
                                        page_size=(w, h),
                                        position=(15, h - 12))

            pdf_bytes_list = [watermark_bytes] * copies
            merged_pdf_bytes = await self.__concat_pdf(pdf_bytes_list)
            # Add page numbers
            pdf_with_page_numbers = await self.__add_page_numbers(
                merged_pdf_bytes,
                page_list=None,
                position=(w / 2 + 50, 10),
            )
            pdf_with_page_numbers = utilpdf.compress_vector_pdf_fiz(pdf_with_page_numbers)
            b64_str = utilpdf.pdf_to_str(pdf_with_page_numbers)
        except Exception as e:
            logger.error(f"Failed to initial printing: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        # Update print count
        pr_file.print_count += 1
        pr_file.last_printed_at = datetime.datetime.now()
        pr_file.last_printed_by = "unknown"
        await pr_file.save()
        updated_file = await self.get_print_file_by_id(id)
        updated_file = await PrintFile_Pydantic.from_tortoise_orm(updated_file)
        results = {
            "file": updated_file,
            "pdf": b64_str
        }
        return results

    def __bytes_to_hash(self, content: bytes) -> str:
        md5_hash = hashlib.md5(content).hexdigest()
        return md5_hash

    async def add_print_file(self, body: PrintFileAddRequest):
        logger.info(f"add_print_file: {body}")
        file_path = UPLOAD_DIR + body.file_path
        related_path = body.file_path
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
                updated_at=now_,
                archived=False,
            )
            logger.info(f"File already exists: id={print_file.id}")
            logger.info(f"File updated: body={body.dict(exclude_unset=True)}")
            return await PrintFileModel.get(id=print_file.id)

        # Add file to database
        print_file = await PrintFileModel.create(
            file_name=file_name,
            file_path=related_path,
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


    async def __add_watermark_to_pdf(self, *args, **kwargs):
        return await asyncio.to_thread(
            utilpdf.add_watermark,
            *args,
            **kwargs
        )

    async def __concat_pdf(self, *args, **kwargs):
        return await asyncio.to_thread(
            utilpdf.concat_pdfs_fitz,
            *args,
            **kwargs
        )

    async def __add_page_numbers(self, *args, **kwargs):
        return await asyncio.to_thread(
            utilpdf.add_page_numbers_fitz,
            *args,
            **kwargs
        )








