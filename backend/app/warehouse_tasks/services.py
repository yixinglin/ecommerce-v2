from datetime import datetime, timedelta
from starlette.exceptions import HTTPException
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.transactions import atomic
from app import WarehouseTaskModel
from app.warehouse_tasks.enums import TaskStatus
from app.warehouse_tasks.models import WarehouseTaskModel_Pydantic, WarehouseTaskActionLog, \
    WarehouseTaskActionLog_Pydantic
from app.warehouse_tasks.schemas import WarehouseTaskPayload, TaskQuery, TaskActionPayload, TaskActionLogQuery
from app.warehouse_tasks.state_machine import TaskStateMachine
from core.response import ListResponse
from tortoise.timezone import now



@atomic()
async def generate_task_code() -> str:
    """
    生成任务唯一 code
    示例：WT2400001, WT2400002
    """
    prefix = "WT"
    date_part = datetime.now().strftime("%y")  # 24

    # 查找当月最大的 code
    latest = await WarehouseTaskModel.filter(
        code__startswith=f"{prefix}{date_part}"
    ).order_by("-code").first()

    if latest:
        # 取最后 5 位数字
        last_num = int(latest.code[-5:])
        num_part = f"{last_num + 1:05d}"
    else:
        num_part = "00001"

    return f"{prefix}{date_part}{num_part}"

class WarehouseTaskService:

    def __init__(self):
        pass

    @atomic()
    async def create_task(self, task_data: WarehouseTaskPayload) -> WarehouseTaskModel:
        task_data.status = TaskStatus.PENDING
        task_data.code = await generate_task_code()
        task_data.active = True
        task_dict = task_data.dict()
        task = await WarehouseTaskModel.create(**task_dict)
        return task

    def __on_status_change(self, task: WarehouseTaskModel, new_status: int):
        if new_status == TaskStatus.EXCEPTION:
            task.is_exception = True
        else:
            task.is_exception = False
            task.exception_type = None

        # if new_status == TaskStatus.PENDING:
        #     task.executing_at = None
        #     task.completed_at = None
        #     task.ready_at = None
        # elif new_status == TaskStatus.PROCESSING:
        #     task.executing_at = now()
        # elif new_status == TaskStatus.READY:
        #     task.ready_at = now()
        # elif new_status == TaskStatus.SHIPPED or new_status == TaskStatus.COMPLETED:
        #     task.completed_at = now()

    @atomic()
    async def update_task(self, task_id, task_data: WarehouseTaskPayload):
        task = await self.get_task(task_id)

        # 状态变化
        if task_data.status != task.status:
            self.__on_status_change(task, task_data.status)

        # 预处理
        if task_data.status != TaskStatus.EXCEPTION:
            task_data.exception_type = None

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

    async def list_tasks(self, request: TaskQuery) -> ListResponse[WarehouseTaskModel_Pydantic]:
        filters = Q()

        if request.status:
            filters &= Q(status=request.status)
        if request.status_not_in:
            filters &= ~Q(status__in=request.status_not_in)
        if request.only_open:
            filters &= ~Q(status__in=[
                TaskStatus.CANCELED,
                TaskStatus.COMPLETED,
            ])
        if request.shop_id:
            filters &= Q(shop_id=request.shop_id)
        if request.type:
            filters &= Q(type=request.type)
        if request.label_type:
            filters &= Q(label_type=request.label_type)
        if request.exception_type:
            filters &= Q(exception_type=request.exception_type)
        if request.priority:
            filters &= Q(priority=request.priority)
        if request.created_from:
            filters &= Q(created_at__gte=request.created_from)
        if request.deadline_to:
            filters &= Q(deadline_at__lte=request.deadline_to)
        if request.priority_from:
            filters &= Q(priority__gte=request.priority_from)
        if request.code is not None and request.code != "":
            filters &= Q(code=request.code)

        if request.keyword is not None and request.keyword != "":
            filters &= (
                    Q(subject__icontains=request.keyword)
                    | Q(code__icontains=request.keyword)
                    | Q(description__icontains=request.keyword)
                    | Q(remark__icontains=request.keyword)
                    | Q(comment__icontains=request.keyword)
                    | Q(executor__icontains=request.keyword)
                    | Q(created_by__icontains=request.keyword)
                )

        total = await WarehouseTaskModel.filter(filters).count()
        offset = (request.page - 1) * request.limit
        limit = request.limit
        tasks = await (WarehouseTaskModel
                       .filter(filters)
                       .limit(limit)
                       .offset(offset)
                       .order_by("deadline_at"))

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

    @atomic()
    async def reset_task(self, task_id):
        task = await self.get_task(task_id)
        if task.status not in [TaskStatus.CANCELED, TaskStatus.EXCEPTION]:
            raise HTTPException(status_code=400, detail="Only canceled or exception tasks can be reset")

        task.status = TaskStatus.PENDING
        task.priority = 3
        task.exception_type = None
        task.is_exception = False
        task.executing_at = None
        task.completed_at = None
        task.deadline_at = now() + timedelta(hours=4)
        task.ready_at = None
        task.active = True
        task.comment = None
        task.executor = None
        await task.save()
        return task

    async def perform_action(self, task_id: int, request: TaskActionPayload):
        task = await self.get_task(task_id)
        await TaskStateMachine.perform_action(
            task,
            action=request.action,
            comment=request.comment,
            operator=request.operator,
            exception_type=request.exception_type,
        )
        return task


class TaskActionLogService:

    async def list_logs(self, query: TaskActionLogQuery) -> ListResponse[WarehouseTaskActionLog_Pydantic]:

        filters = Q()
        if query.task_id:
            filters &= Q(task_id=query.task_id)
        if query.task_code:
            filters &= Q(task_code=query.task_code)
        if query.operator:
            filters &= Q(operator=query.operator)
        if query.action:
            filters &= Q(action=query.action)
        if query.start_time:
            filters &= Q(created_at__gte=query.start_time)
        if query.end_time:
            filters &= Q(created_at__lte=query.end_time)

        total = await WarehouseTaskActionLog.filter(filters).count()

        offset = (query.page - 1) * query.limit
        limit = query.limit
        items = await (WarehouseTaskActionLog
            .filter(filters)
            .limit(limit)
            .offset(offset)
            .order_by("-created_at"))

        results = []
        for item in items:
            results.append(await WarehouseTaskActionLog_Pydantic.from_tortoise_orm(item))

        return ListResponse(
            total=total,
            offset=offset,
            limit=limit,
            data=results
        )

    async def get_available_actions(self, task_id: int):
        """
            {task.actions
              .filter(a => a.visible)
              .map(a => (
                <Button
                  key={a.key}
                  type={a.type}
                  danger={a.danger}
                  disabled={!a.enabled}
                  onClick={() => handleAction(task.id, a.key)}
                >
                  {a.label}
                </Button>
            ))}

        :param task_id:
        :return:
        """
        try:
            task = await WarehouseTaskModel.get(id=task_id)
        except DoesNotExist as e:
            raise ValueError(f"Task {task_id} not found")

        return TaskStateMachine.get_available_actions(task)