import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from app.reply_handler.enums import ActionType, EmailCategory, EmailStatus

class PullEmailsRequest(BaseModel):
    limit: Optional[int] = 20

class EmailsQueryRequest(BaseModel):
    keyword: Optional[str] = None
    category: Optional[EmailCategory] = None
    status: Optional[EmailStatus] = None
    action_type: Optional[ActionType] = None
    page: int = 1
    limit: int = 10

class EmailBaseResponse(BaseModel):
    id: int
    sender: str
    sender_name: Optional[str]
    subject: str

    received_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime

    recipient: Optional[str]

    category: Optional[EmailCategory]
    status: Optional[EmailStatus]
    action_type: Optional[ActionType]

    ai_result_text: Optional[str]


class EmailResponse(EmailBaseResponse):
    body: str


class ProcessEmailRequest(BaseModel):
    category: Optional[EmailCategory] = None
    note: Optional[str] = None
    old_email: Optional[EmailStr] = None
    new_email: Optional[EmailStr] = None
    user: str = Field(..., description="执行操作的用户名")


