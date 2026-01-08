from enum import IntEnum

from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel



class ErrorCode(IntEnum):
    SUCCESS = 10000

    # 通用 20xxx
    PARAM_ERROR = 20001
    PARAM_MISSING = 20002
    BAD_REQUEST = 20003

    # 权限 30xxx
    UNAUTHORIZED = 30001
    FORBIDDEN = 30002

    # 用户 41xxx
    USER_NOT_FOUND = 41001
    USER_ALREADY_EXISTS = 41002

    # 服务器
    SERVER_ERROR = 50000




T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    code: int = ErrorCode.SUCCESS
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, msg: str = "success"):
        return cls(
            code=ErrorCode.SUCCESS,
            message=msg,
            data=data
        )

    @classmethod
    def fail(cls, code: ErrorCode, msg: str = None):
        return cls(
            code=code,
            message=msg or code.name,
            data=None
        )

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int