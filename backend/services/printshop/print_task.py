import datetime
from typing import List

from fastapi import HTTPException
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from models import PrintTaskModel, PrintLogModel
from models.print_task import PrintTask_Pydantic, PrintStatus, PrintLog_Pydantic


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
