from http.client import HTTPException

from fastapi import APIRouter

from app.warehouse_tasks.enums import ENUM_REGISTRY as WTM_ENUM_REGISTRY

enum_router = APIRouter()

ENUM_REGISTRY = {}

ENUM_REGISTRY.update(WTM_ENUM_REGISTRY)

@enum_router.get("/{enum_name}")
async def get_enum(enum_name: str):
    enum_cls = ENUM_REGISTRY.get(enum_name)
    if not enum_cls:
        raise HTTPException(status_code=404, detail="Enum not found")
    return enum_cls.dict()