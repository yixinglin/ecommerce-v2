import datetime
from typing import Optional
from pydantic import BaseModel

class VersionInfoResponse(BaseModel):
    app_name: str
    version: str
    file_path: str
    changelog: Optional[str] = None
    md5: Optional[str] = None
    created_at: datetime.datetime
    is_latest: Optional[bool] = None


class VersionInfoUpdate(BaseModel):
    app_name: str
    version: str
    file_path: str
    changelog: Optional[str] = None