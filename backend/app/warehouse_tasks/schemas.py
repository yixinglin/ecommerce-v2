from typing import Optional, Dict, Any, List
import datetime

from fastapi import Query
from pydantic import BaseModel, Field

class TaskQueryRequest(BaseModel):
    status: Optional[int] = None
    status_not_in: Optional[List[int]] = None
    shop_id: Optional[int] = None
    priority: Optional[int] = None
    priority_from: Optional[int] = None
    created_from: Optional[datetime.datetime] = None
    deadline_to: Optional[datetime.datetime] = None
    page: int = Query(default=1, ge=1)
    limit: int = Query(default=20, ge=1, le=500)


class WarehouseTaskPayload(BaseModel):
    deadline_at: Optional[datetime.datetime] = None
    priority: int = Field(default=3, ge=1, le=5)
    shop_id: Optional[int] = Field(default=None, ge=0)
    status: Optional[int] = Field(default=None, ge=0)
    type: Optional[int] = Field(default=None, ge=0)
    label_type: Optional[int] = Field(default=None, ge=0)
    active: Optional[bool] = None

    subject: Optional[str] = None
    description: Optional[str] = None
    remark: Optional[str] = None
    comment: Optional[str] = None

    executor: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
