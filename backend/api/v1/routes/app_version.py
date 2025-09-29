from typing import List

from fastapi import APIRouter

from app.app_versions.schemas import VersionInfoResponse, VersionInfoUpdate
from app.app_versions.services import AppVersionService

app_version_router = APIRouter()

@app_version_router.get(
    "/{app_name}/latest",
    response_model=VersionInfoResponse
)
async def get_latest_version(app_name: str):
    service = AppVersionService()
    return await service.get_latest_version(app_name)

@app_version_router.get(
    "/{app_name}/{version}",
    response_model=VersionInfoResponse
)
async def get_version_info(app_name: str, version: str) -> VersionInfoResponse:
    service = AppVersionService()
    return await service.get_version_info(app_name, version)

@app_version_router.get(
    "/{app_name}",
    response_model=List[VersionInfoResponse]
)
async def get_all_versions(app_name: str) -> List[VersionInfoResponse]:
    service = AppVersionService()
    vers = await service.get_all_versions(app_name)
    return vers

@app_version_router.post(
    "/{app_name}",
    response_model=VersionInfoResponse
)
async def update_new_version(update_data: VersionInfoUpdate) -> VersionInfoResponse:
    service = AppVersionService()
    return await service.update_new_version(update_data)
