from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from models.base import TortoiseBasicModel


class WarehouseTaskModel(TortoiseBasicModel):
    """
    仓库任务表
    """
    id = fields.BigIntField(pk=True)
    code = fields.CharField(max_length=64, description="任务编号")

    # 基础属性
    deadline_at = fields.DatetimeField(description="截至时间")
    priority = fields.IntField(default=3, description="优先级（1-5，数值越大优先级越高）")
    shop_id = fields.IntField(null=True, description="商铺（枚举）")
    status = fields.IntField(description="任务状态（TaskStatus 枚举）")
    type = fields.IntField(description="任务类型（TaskType 枚举）")
    label_type = fields.IntField(null=True, description="贴码类型（透明码 / FBA码）")
    active = fields.BooleanField(default=True, description="是否有效")

    # 任务内容
    subject = fields.CharField(max_length=255, description="任务主题")
    description = fields.TextField(null=True, description="任务描述")
    remark = fields.TextField(null=True, description="任务备注")
    comment = fields.TextField(null=True, description="任务留言")

    # 执行信息
    executor = fields.CharField(max_length=20, null=True, description="任务执行人")
    executing_at = fields.DatetimeField(null=True,description="任务执行时间（进入备货中的时间）")
    completed_at = fields.DatetimeField(null=True, description="任务完成时间（已备好的时间）")

    # 附件
    documents = fields.TextField(null=True, description="上传的相关文档")
    images = fields.TextField(null=True, description="上传的相关图片")

    # 扩展字段
    extra = fields.JSONField(null=True, description="扩展字段")

    class Meta:
        table = "wtm_tasks"
        description = "Warehouse Task Model"


WarehouseTaskModel_Pydantic = pydantic_model_creator(WarehouseTaskModel, name="WarehouseTaskModel")



