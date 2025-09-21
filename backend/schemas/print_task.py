from typing import Optional

from pydantic import BaseModel


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
