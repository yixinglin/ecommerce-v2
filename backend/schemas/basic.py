from enum  import Enum
from typing import Any
from pydantic import BaseModel, Field

class CodeEnum(str, Enum):
    Success = 200
    Fail = 400
    Unauthorized = 401
    Forbidden = 403
    NotFound = 404
    InternalServerError = 500

class BasicResponse(BaseModel):
    code: CodeEnum = Field( default=CodeEnum.Success, description="Response code")
    message: str = Field(default="Requst successful", description="Response message")
    data: Any = Field(default=None, description="Response data")

class ResponseSuccess(BasicResponse):
    pass

class ResponseFail(BasicResponse):
    code: CodeEnum = Field(default=CodeEnum.Fail, description="Response code")
    message: str = Field(default="Request failed", description="Response message")
    data: Any = Field(default=None, description="Response data")

class ResponseUnauthorized(BasicResponse):
    code: CodeEnum = Field(default=CodeEnum.Unauthorized, description="Response code")
    message: str = Field(default="Unauthorized", description="Response message")
    data: Any = Field(default=None, description="Response data")

class ResponseNotFound(BasicResponse):
    code: CodeEnum = Field(default=CodeEnum.NotFound, description="Response code")
    message: str = Field(default="Not found", description="Response message")


