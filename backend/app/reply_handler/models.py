# ---------- 主模型 ----------
from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from app.reply_handler.enums import EmailCategory, EmailStatus, ActionType
from models.base import TortoiseBasicModel


class EmailInboxModel(TortoiseBasicModel):
    id = fields.IntField(pk=True)
    message_id = fields.CharField(max_length=255, unique=True)
    sender = fields.CharField(max_length=255, description="发件人")
    sender_name = fields.CharField(max_length=255, null=True, description="发件人姓名")
    recipient = fields.CharField(max_length=1024, description="收件人")
    subject = fields.CharField(max_length=512, description="主题")
    body = fields.TextField()
    received_at = fields.DatetimeField(description="接收时间")
    # 冗余字段
    action_type = fields.CharEnumField(ActionType, null=True, max_length=30, description="操作类型")

    ai_result_text = fields.TextField(null=True, description="AI识别结果")
    category = fields.CharEnumField(EmailCategory, null=True, max_length=50, description="邮件类别")
    status = fields.CharEnumField(EmailStatus, default=EmailStatus.unprocessed, max_length=30, description="邮件状态")

    class Meta:
        table = "rhl_email_inbox"

    def __str__(self):
        return f"[{self.id}] {self.sender} - {self.subject}"

EmailInboxModel_Pydantic = pydantic_model_creator(EmailInboxModel, name="EmailInboxModel")

# ---------- 操作记录模型 ----------
class EmailActionModel(TortoiseBasicModel):
    id = fields.IntField(pk=True)
    email_inbox_id = fields.IntField()

    action_type = fields.CharEnumField(ActionType, max_length=30, description="操作类型")
    note = fields.CharField(null=True, max_length=512, description="操作备注")

    old_email = fields.CharField(max_length=255, null=True, description="旧邮箱地址")
    new_email = fields.CharField(max_length=255, null=True, description="新邮箱地址")

    user = fields.CharField(max_length=100, null=True, description="操作人")

    class Meta:
        table = "rhl_email_actions"

    def __str__(self):
        return f"[{self.id}] {self.action_type} by {self.user}"

EmailActionModel_Pydantic = pydantic_model_creator(EmailActionModel, name="EmailActionModel")


class ProcessedAddressModel(TortoiseBasicModel):
    id = fields.IntField(pk=True)
    sender = fields.CharField(max_length=255, unique=True, description="发件人邮箱")
    sender_name = fields.CharField(max_length=255, null=True, description="发件人姓名")
    last_category = fields.CharEnumField(EmailCategory, max_length=50, description="邮件类别")
    last_note = fields.CharField(null=True, max_length=512, description="操作备注")
    last_new_email = fields.CharField(max_length=255, null=True, description="发件人新邮箱地址")
    last_action_id = fields.IntField(description="关联的操作记录ID")
    action_count = fields.IntField(default=0, description="操作次数")

    class Meta:
        table = "rhl_processed_addresses"

    def __str__(self):
        return f"[{self.id}] {self.email} - {self.last_category}"

ProcessedAddressModel_Pydantic = pydantic_model_creator(ProcessedAddressModel, name="ProcessedAddressModel")