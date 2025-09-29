from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from models.base import TortoiseBasicModel

class AppVersion(TortoiseBasicModel):
    id = fields.IntField(pk=True)
    app_name = fields.CharField(max_length=100, description="Name of the app")
    version = fields.CharField(max_length=20, description="Version of the app")
    file_path = fields.CharField(max_length=255, description="Path of the app file")
    changelog = fields.TextField(null=True, description="Changelog of the app")
    md5 = fields.CharField(max_length=64, null=True, description="MD5 hash of the app file")
    is_latest = fields.BooleanField(default=False, description="Is this the latest version of the app")

    class Meta:
        table = "app_versions"

AppVersion_Pydantic = pydantic_model_creator(AppVersion, name="AppVersion")