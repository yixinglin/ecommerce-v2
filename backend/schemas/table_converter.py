from typing import List, Optional

from pydantic import BaseModel

from models.table_converter import DataType


class TemplateAddRequest(BaseModel):
    name: str
    remark: Optional[str] = ""
    channel: str
    type: str
    updated_by: str
    created_by: str

class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    remark: Optional[str] = None
    channel: Optional[str] = None
    type: Optional[str] = None
    updated_by: Optional[str] = None

class TemplateFieldAddRequest(BaseModel):
    field_name: str
    display_name: str = None
    type: Optional[DataType] = DataType.Any
    order_index: Optional[int] = 0
    formula: Optional[str] = None
    updated_by: Optional[str] = None
    created_by: Optional[str] = None

class TemplateFieldUpdateRequest(BaseModel):
    field_name: Optional[str] = None
    display_name: Optional[str] = None
    type: Optional[DataType] = None
    order_index: Optional[int] = None
    formula: Optional[str] = None
    updated_by: Optional[str] = None

class MappingPairAddRequest(BaseModel):
    source_field_id: int
    target_field_id: int

class MappingAddRequest(BaseModel):
    source_template_id: int
    target_template_id: int
    name: Optional[str] = ""
    remark: Optional[str] = ""
    updated_by: Optional[str] = None
    created_by: Optional[str] = None
    pairs: List[MappingPairAddRequest]