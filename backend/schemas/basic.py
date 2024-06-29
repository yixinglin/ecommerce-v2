from enum  import Enum
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class CodeEnum(str, Enum):
    Success = 200
    Fail = 400
    Unauthorized = 401
    Forbidden = 403
    NotFound = 404
    InternalServerError = 500

class BasicResponse(BaseModel, Generic[T]):
    code: CodeEnum = Field(default=CodeEnum.Success, description="Response code")
    message: str = Field(default="Request successful", description="Response message")
    data: T = Field(default=None, description="Response data")

class ResponseSuccess(BasicResponse):
    pass

class ResponseFailure(BasicResponse):
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

class ExternalService(str, Enum):
    Amazon = "amazon",
    Kaufland = "kaufland",
    Gls = "gls",
    Ebay = "ebay"



