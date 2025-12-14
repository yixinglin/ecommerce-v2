from typing import Optional, List

from pydantic import BaseModel

from app.printshop.models.print_task import PrintStatus


class PrintFileAddRequest(BaseModel):
    file_name: str
    file_path: str

class PrintFileUpdateRequest(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    archived: Optional[bool] = None
    print_count: Optional[int] = None

class PrintTaskCreate(BaseModel):
    task_name: str
    created_by: str
    description: Optional[str] = None
    file_paths: Optional[List[str]] = None

class PrinteTaskUpdate(BaseModel):
    task_name: Optional[str] = None
    created_by: Optional[str] = None
    printed_by: Optional[str] = None
    status: Optional[PrintStatus] = PrintStatus.NOT_PRINTED
    file_paths: Optional[List[str]] = None
    description: Optional[str] = None
    skip: Optional[int] = None
    signature: Optional[str] = None