from enum import  IntEnum
from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from models.base import TortoiseBasicModel


class PrintStatus(IntEnum):
    NOT_PRINTED = 0
    PRINTING = 1
    PRINTED = 2
    CANCELLED = 3

class PrintTaskModel(models.Model):
    id = fields.IntField(primary_key=True)
    task_name = fields.CharField(max_length=200, description="Name of the print task")
    description = fields.TextField(default="", description="Description of the print task")
    file_paths = fields.CharField(max_length=1000, default="", description="Semicolon separated file paths")
    skip = fields.IntField(default=0, description="Number of files to skip")
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


# -------------- Print File Model ---------------
class PrintFileModel(TortoiseBasicModel):
    id = fields.IntField(pk=True)
    file_name = fields.CharField(max_length=200, description="Name of the file")
    file_path = fields.CharField(max_length=350, description="Path of the file")
    file_hash = fields.CharField(max_length=32, description="Hash of the file")
    file_size = fields.IntField(description="Size of the file in bytes")
    file_pages = fields.IntField(description="Number of pages in the file")
    file_type = fields.CharField(max_length=20, description="Type of the file")
    file_extension = fields.CharField(max_length=10, description="Extension of the file")
    owner = fields.CharField(default="unknown", max_length=50, description="Owner of the file")
    description = fields.TextField(default="", description="Description of the file")
    archived = fields.BooleanField(default=False, description="Whether the file is archived or not")
    print_count = fields.IntField(default=0, description="Number of times the file was printed")
    last_printed_at = fields.DatetimeField(null=True, description="Date and time when the file was last printed")
    last_printed_by = fields.CharField(max_length=50, default="", description="User who last printed the file")

    class Meta:
        table = "print_file"

PrintFile_Pydantic = pydantic_model_creator(PrintFileModel, name="PrintFile")

