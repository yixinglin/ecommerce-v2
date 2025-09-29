import hashlib
import os
from typing import List
from packaging import version
from starlette.exceptions import HTTPException
from tortoise.transactions import in_transaction

from app import AppVersion
from app.app_versions.models import AppVersion_Pydantic
from app.app_versions.schemas import VersionInfoResponse, VersionInfoUpdate
from core.config2 import settings
from core.log import logger

UPLOAD_DIR = settings.static.upload_dir

class AppVersionService:
    def __init__(self):
        pass

    async def get_latest_version(self, app_name: str) -> VersionInfoResponse:
        version = await AppVersion.filter(app_name=app_name, is_latest=True).first()
        if not version:
            raise HTTPException(status_code=404, detail="No version found")
        return await AppVersion_Pydantic.from_tortoise_orm(version)

    async def get_version_info(self, app_name: str, version: str) -> VersionInfoResponse:
        version = await AppVersion.filter(app_name=app_name, version=version).first()
        if not version:
            raise HTTPException(status_code=404, detail="No version found")
        return await AppVersion_Pydantic.from_tortoise_orm(version)

    async def get_all_versions(self, app_name: str) -> List[VersionInfoResponse]:
        versions = await AppVersion.filter(app_name=app_name).all().order_by("-id")
        return [await AppVersion_Pydantic.from_tortoise_orm(version) for version in versions]

    async def update_new_version(self, update_data: VersionInfoUpdate) -> VersionInfoResponse:
        save_path = UPLOAD_DIR + update_data.file_path
        logger.info(f"Saving file to {save_path}")
        # Check if zip
        if not save_path.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Upload package must be a zip file")
        # Check if file exists
        if not os.path.exists(save_path):
            raise HTTPException(status_code=400, detail="Upload package not found")

        # ===== Verify version =====
        latest = await AppVersion.filter(app_name=update_data.app_name, is_latest=True).first()
        if latest:
            try:
                if version.parse(update_data.version) <= version.parse(latest.version):
                    raise HTTPException(
                        status_code=400,
                        detail=f"New version ({update_data.version}) must be greater than current latest ({latest.version})"
                    )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Version format error: {e}")

        with open(save_path, 'rb') as f:
            content = f.read()

        # Compute md5
        md5 = hashlib.md5(content).hexdigest()

        async with in_transaction():
            # 取消旧版本的is_latest
            await AppVersion.filter(app_name=update_data.app_name, is_latest=True).update(is_latest=False)
            # 保存新版本
            new_version = await AppVersion.create(
                is_latest=True,
                md5=md5,
                **update_data.dict(exclude_unset=True)
            )
        return await AppVersion_Pydantic.from_tortoise_orm(new_version)




