from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator


class SKUReplenishmentProfileModel(models.Model):
    """
    SKU Replenishment Profile:
    This model stores per-SKU replenishment configurations, such as lead time,
    active status, and brand information. It controls whether the SKU appears
    in replenishment reports and how its demand is calculated.
    """
    id = fields.IntField(pk=True)
    local_sku = fields.CharField(max_length=30, unique=True, description="Local SKU in Lingxing")
    brand = fields.CharField(max_length=80, default="Unknown Brand", description="Brand name")
    lead_time = fields.FloatField(default=1.5, description="Lead time in months")
    image = fields.CharField(max_length=255, default="", description="Image URL for this SKU")
    product_name = fields.CharField(max_length=255, default="", description="Product name for this SKU")
    units_per_carton = fields.IntField(default=1, description="Number of units per carton")
    remark = fields.CharField(max_length=255, default="", description="Remarks for this profile")
    active = fields.BooleanField(default=True, description="Whether this SKU is active for replenishment reporting")
    created_at = fields.DatetimeField(auto_now_add=True, description="Creation timestamp")
    updated_at = fields.DatetimeField(auto_now=True, description="Last update timestamp")
    created_by = fields.CharField(max_length=50, description="User who created this record")
    updated_by = fields.CharField(max_length=50, description="User who last updated this record")

    class Meta:
        table = "lx_sku_replenishment_profile"
        ordering = ["id"]
        table_description = "Per-SKU replenishment configuration for forecasting and reporting"

SKUReplenishmentProfile_Pydantic = pydantic_model_creator(SKUReplenishmentProfileModel, name="SKUReplenishmentProfile")

