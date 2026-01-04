import random
import string
from datetime import datetime

from starlette.exceptions import HTTPException
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.transactions import atomic

from app import WarehouseTaskModel
from app.warehouse_tasks.enums import TaskStatus
from app.warehouse_tasks.models import WarehouseTaskModel_Pydantic
from app.warehouse_tasks.schemas import WarehouseTaskPayload, TaskQueryRequest
from core.response import ListResponse


def generate_task_code(prefix: str = "WT") -> str:
    """
    生成任务唯一 code
    示例：WT-20240618-K9F3X2
    """
    date_part = datetime.now().strftime("%y%m%d")
    rand_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=5)
    )
    return f"{prefix}-{date_part}-{rand_part}"


class WarehouseTaskService:

    def __init__(self):
        pass

    @atomic()
    async def create_task(self, task_data: WarehouseTaskPayload) -> WarehouseTaskModel:
        task_dict = task_data.dict()
        task_dict['code'] = generate_task_code()
        task = await WarehouseTaskModel.create(**task_dict)
        return task

    @atomic()
    async def update_task(self, task_id, task_data: WarehouseTaskPayload):
        task = await self.get_task(task_id)

        for field, value in task_data.dict(exclude_unset=True).items():
            if hasattr(task, field):
                setattr(task, field, value)

        await task.save()
        return task

    async def get_task(self, task_id) -> WarehouseTaskModel:
        try:
            task = await WarehouseTaskModel.get(id=task_id)
        except DoesNotExist:
            raise ValueError(f"Task {task_id} not found")
        return task

    async def list_tasks(self, request: TaskQueryRequest) -> ListResponse[WarehouseTaskModel_Pydantic]:
        filters = Q()

        if request.status:
            filters &= Q(status=request.status)
        if request.status_not_in:
            filters &= ~Q(status__in=request.status_not_in)
        if request.shop_id:
            filters &= Q(shop_id=request.shop_id)
        if request.priority:
            filters &= Q(priority=request.priority)
        if request.created_from:
            filters &= Q(created_at__gte=request.created_from)
        if request.deadline_to:
            filters &= Q(deadline_at__lte=request.deadline_to)
        if request.priority_from:
            filters &= Q(priority__gte=request.priority_from)

        total = await WarehouseTaskModel.filter(filters).count()
        offset = (request.page - 1) * request.limit
        limit = request.limit
        tasks = await (WarehouseTaskModel
                       .filter(filters)
                       .limit(limit)
                       .offset(offset)
                       .order_by("-deadline_at"))


        results = []
        for task in tasks:
            results.append(await WarehouseTaskModel_Pydantic.from_tortoise_orm(task))

        resp = ListResponse(
            total=total,
            offset=offset,
            limit=limit,
            data=results
        )
        return resp


    @atomic()
    async def delete_task(self, task_id):
        task = await self.get_task(task_id)
        if task.status != TaskStatus.PENDING:
            await task.delete()
        else:
            raise HTTPException(status_code=400, detail="Only pending tasks can be deleted")
