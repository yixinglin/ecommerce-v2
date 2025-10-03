from pydantic import BaseModel
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class ListResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    offset: int
    limit: int

