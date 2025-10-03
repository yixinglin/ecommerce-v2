import io
from typing import TypeVar, Generic, List, Dict

import pandas as pd
from fastapi import APIRouter, Body, File, UploadFile, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.printshop.models.table_converter import Template_Pydantic, TemplateField_Pydantic, \
    Mapping_Pydantic, MappingPair_Pydantic
from app.printshop.schames.table_converter import TemplateAddRequest, MappingAddRequest, TemplateFieldAddRequest, \
    TemplateUpdateRequest, TemplateFieldUpdateRequest
from app.printshop.services.table_converter import TableConvertService

tc_router = APIRouter()

T = TypeVar('T')

class ListResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    offset: int
    limit: int


"""
模板管理（Template）

"""
TemplateListResponse = ListResponse[Template_Pydantic]
ChannelListResponse = ListResponse[str]
TemplateTypeListResponse = ListResponse[str]

@tc_router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="Get templates",
    description="Get a list of templates",
)
async def get_templates(
    limit: int = 10,
    offset: int = 0,
):

    service = TableConvertService()
    templates = await service.query_templates(
        limit=limit,
        offset=offset
    )

    return TemplateListResponse(
        data=templates,
        total=len(templates),
        offset=offset,
        limit=limit
    )


@tc_router.post(
    "/templates",
    response_model=Template_Pydantic,
    summary="Add a template",
    description="Add a new template",
)
async def add_template(body: TemplateAddRequest = Body(...)):
    service = TableConvertService()
    template = await service.add_template(body)
    return template

@tc_router.put(
    "/templates/{template_id}",
    response_model=Template_Pydantic,
    summary="Update a template",
    description="Update a template by ID",
)
async def update_template(template_id: int, body: TemplateUpdateRequest = Body(...)):
    service = TableConvertService()
    template = await service.update_template(template_id, body)
    return template

@tc_router.delete(
    "/templates/{template_id}",
    response_model=Dict,
    summary="Delete a template",
    description="Delete a template by ID",
)
async def delete_template(template_id: int):
    service = TableConvertService()
    result = await service.delete_template(template_id)
    return {
        "data": result
    }

@tc_router.get(
    "/templates/channels",
    response_model=ChannelListResponse,
    summary="Get template channels",
    description="Get a list of supported template channels",
)
async def get_template_channel_list():
    service = TableConvertService()
    channels = await service.get_template_channel_list()
    return ChannelListResponse(
        data=channels,
        total=len(channels),
        offset=0,
        limit=len(channels)
    )

@tc_router.get(
    "/templates/types",
    response_model=TemplateTypeListResponse,
    summary="Get template types",
    description="Get a list of supported template types",
)
async def get_template_type_list():
    service = TableConvertService()
    types = await service.get_template_type_list()
    return TemplateTypeListResponse(
        data=types,
        total=len(types),
        offset=0,
        limit=len(types)
    )

"""
模板字段管理（Template Field）

"""
TemplateFieldListResponse = ListResponse[TemplateField_Pydantic]
FieldTypeListResponse = ListResponse[str]

@tc_router.get(
    "/templates/{template_id}/fields",
    response_model=TemplateFieldListResponse,
    summary="Get template fields",
    description="Get a list of fields for a template",
)
async def get_template_fields(template_id: int):
    service = TableConvertService()
    fields = await service.query_template_fields(template_id)
    return TemplateFieldListResponse(
        data=fields,
        total=len(fields),
        offset=0,
        limit=len(fields)
    )

@tc_router.post(
    "/templates/{template_id}/fields",
    response_model=TemplateField_Pydantic,
    summary="Add a template field",
    description="Add a new field to a template",
)
async def add_template_field(template_id: int, body: TemplateFieldAddRequest):
    service = TableConvertService()
    field = await service.add_template_field(template_id, body)
    return field

@tc_router.put(
    "/templates/fields/{field_id}",
    response_model=TemplateField_Pydantic,
    summary="Update a template field",
    description="Update a field in a template",
)
async def update_template_field(field_id: int, body: TemplateFieldUpdateRequest):
    service = TableConvertService()
    field = await service.update_template_field(field_id, body)
    return field

@tc_router.delete(
    "/templates/fields/{field_id}",
    response_model=Dict,
    summary="Delete a template field",
    description="Delete a field from a template",
)
async def delete_template_field(field_id: int):
    service = TableConvertService()
    result = await service.delete_template_field(field_id)
    return {
        "data": result
    }

@tc_router.get(
    "/templates/field-types",
    response_model=FieldTypeListResponse,
    summary="Get field types",
    description="Get a list of supported field types",
)
async def get_field_type_list():
    service = TableConvertService()
    field_types = await service.get_field_type_list()
    return FieldTypeListResponse(
        data=field_types,
        total=len(field_types),
        offset=0,
        limit=len(field_types)
    )


"""
字段映射管理（Mapping）

"""
@tc_router.get(
    "/mappings",
    response_model=Mapping_Pydantic,
    summary="Get mapping",
    description="Get a mapping between two templates",
)
async def get_mapping(source_template_id: int, target_template_id: int):
    service = TableConvertService()
    mapping = await service.query_mapping(source_template_id, target_template_id)
    return mapping

MappingPairListResponse = ListResponse[MappingPair_Pydantic]

@tc_router.get(
    "/mappings/{mapping_id}/pairs",
    response_model=MappingPairListResponse,
    summary="Get mapping pairs",
    description="Get a list of mapping pairs for a mapping",
)
async def get_mapping_pairs(mapping_id: int):
    service = TableConvertService()
    pairs = await service.query_mapping_pairs(mapping_id)
    return MappingPairListResponse(
        data=pairs,
        total=len(pairs),
        offset=0,
        limit=len(pairs)
    )

@tc_router.post(
    "/mappings",
    response_model=Dict,
    summary="Add a mapping",
    description="Add a new mapping between two templates",
)
async def add_mapping(body: MappingAddRequest):
    service = TableConvertService()
    result = await service.add_mapping(body)
    return {
        "data": result
    }

@tc_router.put(
    "/mappings/{mapping_id}",
    response_model=Dict,
    summary="Update a mapping",
    description="Update a mapping between two templates",
)
async def update_mapping(mapping_id: int, body: MappingAddRequest):
    service = TableConvertService()
    result = await service.update_mapping(mapping_id, body)
    return {
        "data": result
    }


import uuid

@tc_router.post(
    "/mappings/{mapping_id}/convert",
    response_model=Dict,
    summary="Convert a table",
    description="Convert a table using a mapping",
)
async def convert_table(mapping_id: int, file: UploadFile = File(...)):
    # Step 1: Load source file
    try:
        source_df = pd.read_excel(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Excel file")

    # Step 2: Convert
    service = TableConvertService()
    try:
        target_df = await service.convert_table(mapping_id, source_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    # Step 3: Write to memory buffer
    buffer = io.BytesIO()
    target_df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)

    # Step 4: Return as stream (no temp file)
    filename = f"{uuid.uuid4().hex}.xlsx"
    return StreamingResponse(
        content=buffer,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
