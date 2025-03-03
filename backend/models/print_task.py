from enum import  IntEnum
from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator


class PrintStatus(IntEnum):
    NOT_PRINTED = 0
    PRINTING = 1
    PRINTED = 2
    CANCELLED = 3

class PrintTaskModel(models.Model):
    id = fields.IntField(primary_key=True)
    task_name = fields.CharField(max_length=200, description="Name of the print task")
    file_paths = fields.CharField(max_length=1000, default="", description="Semicolon separated file paths")
    created_at = fields.DatetimeField(auto_now_add=True, null=True, description="Date and time when the task was created")
    created_by = fields.CharField(max_length=50, description="User who created the task")
    printed_at = fields.DatetimeField(null=True, description="Date and time when the task was printed")
    printed_by = fields.CharField(max_length=50, default="", description="User who printed the document")
    status = fields.IntEnumField(PrintStatus, default=PrintStatus.NOT_PRINTED)
    signature = fields.TextField(default="", description="Base64 encoded signature of the printed document")

    class Meta:
        table = "print_tasks"

# 用于响应返回的 Pydantic 模型（包含只读字段）
PrintTask_Pydantic = pydantic_model_creator(PrintTaskModel, name="PrintTask")

class PrintLogModel(models.Model):
    id = fields.IntField(pk=True)
    task = fields.ForeignKeyField(
        "models.PrintTaskModel",
        related_name="logs",
        description="Associated print task"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="Date and time when the log was created")
    content = fields.CharField(max_length=200, description="Content of the log")

    class Meta:
        table = "print_logs"

# 用于响应返回的 Pydantic 模型（包含只读字段）
PrintLog_Pydantic = pydantic_model_creator(PrintLogModel, name="PrintLog")

"""
api示例

# 创建任务 —— 增（Create）
@app.post("/print-tasks", response_model=PrintTask_Pydantic)
async def create_print_task(task: PrintTaskIn_Pydantic):
    task_obj = await PrintTaskModel.create(**task.dict())
    return await PrintTask_Pydantic.from_tortoise_orm(task_obj)

# 查询任务 —— 查（Retrieve）
@app.get("/print-tasks/{task_id}", response_model=PrintTask_Pydantic)
async def get_print_task(task_id: int):
    try:
        task_obj = await PrintTaskModel.get(id=task_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")
    return await PrintTask_Pydantic.from_tortoise_orm(task_obj)

# 更新任务 —— 更新（Update）
@app.put("/print-tasks/{task_id}", response_model=PrintTask_Pydantic)
async def update_print_task(task_id: int, task: PrintTaskIn_Pydantic):
    try:
        task_obj = await PrintTaskModel.get(id=task_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")
    task_data = task.dict(exclude_unset=True)
    for key, value in task_data.items():
        setattr(task_obj, key, value)
    await task_obj.save()
    return await PrintTask_Pydantic.from_tortoise_orm(task_obj)

# 查询某个打印任务的所有日志
print_task = await PrintTaskModel.get(id=1)
logs = await print_task.logs.all()
"""