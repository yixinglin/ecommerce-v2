from typing import Optional, Dict, Any, List
import datetime

from fastapi import Query
from pydantic import BaseModel, Field

class TaskQuery(BaseModel):
    keyword: Optional[str] = None
    code: Optional[str] = None
    status: Optional[int] = None
    status_not_in: Optional[List[int]] = None
    only_open: Optional[bool] = True
    shop_id: Optional[int] = None
    type: Optional[int] = None
    label_type: Optional[int] = None
    exception_type: Optional[int] = None
    priority: Optional[int] = None
    priority_from: Optional[int] = None
    created_from: Optional[datetime.datetime] = None
    deadline_to: Optional[datetime.datetime] = None
    page: int = Query(default=1, ge=1)
    limit: int = Query(default=20, ge=1, le=500)


class WarehouseTaskPayload(BaseModel):
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    code: Optional[str] = None
    deadline_at: Optional[datetime.datetime] = None
    priority: int = Field(default=3, ge=1, le=5)
    shop_id: Optional[int] = Field(default=None, ge=0)
    status: Optional[int] = Field(default=None, ge=0)
    type: Optional[int] = Field(default=None, ge=0)
    exception_type: Optional[int] = Field(default=None, ge=0)
    label_type: Optional[int] = Field(default=None, ge=0)
    active: Optional[bool] = None

    subject: Optional[str] = None
    description: Optional[str] = None
    remark: Optional[str] = None
    comment: Optional[str] = None

    executor: Optional[str] = None

    documents: Optional[List[str]] = None
    images: Optional[List[str]] = None

    extra: Optional[Dict[str, Any]] = None

class TaskActionPayload(BaseModel):
    action: str
    executor: str
    comment: Optional[str] = None
    exception_type: Optional[int] = None


class TaskActionLogQuery(BaseModel):
    task_id: Optional[int] = None
    task_code: Optional[str] = None
    executor: Optional[str] = None
    action: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None

    page: int = Query(default=1, ge=1)
    limit: int = Query(default=20, ge=1, le=500)


