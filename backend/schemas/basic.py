from enum  import Enum
from typing import Generic, TypeVar, Optional
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
    data: Optional[T] = Field(default=None, description="Response data")

class ResponseSuccess(BasicResponse[T], Generic[T]):
    code: CodeEnum = Field(default=CodeEnum.Success, description="Response code")
    message: str = Field(default="Request successful", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")

class ResponseFailure(BasicResponse[T], Generic[T]):
    code: CodeEnum = Field(default=CodeEnum.Fail, description="Response code")
    message: str = Field(default="Request failed", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")

class ResponseUnauthorized(BasicResponse[T], Generic[T]):
    code: CodeEnum = Field(default=CodeEnum.Unauthorized, description="Response code")
    message: str = Field(default="Unauthorized", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")

class ResponseNotFound(BasicResponse[T], Generic[T]):
    code: CodeEnum = Field(default=CodeEnum.NotFound, description="Response code")
    message: str = Field(default="Not found", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")

class ExternalService(str, Enum):
    Amazon = "amazon",
    Kaufland = "kaufland",
    Gls = "gls",
    Ebay = "ebay"
