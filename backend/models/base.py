from tortoise import fields, models

class TortoiseBasicModel(models.Model):
    created_at = fields.DatetimeField(auto_now_add=True, description="Creation timestamp")
    created_by = fields.CharField(max_length=20, null=True, description="Creator name")
    updated_at = fields.DatetimeField(auto_now=True, description="Last updated timestamp")
    updated_by = fields.CharField(max_length=20, null=True, description="Last updater name")