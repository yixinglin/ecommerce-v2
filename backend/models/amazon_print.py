from enum import  IntEnum
from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator


class TransparencyCodeStatus(IntEnum):
    UNUSED = 0
    USED = 1
    LOCKED = 2
    DELETED = 3
    

class TransparencyCodeModel(models.Model):
    id = fields.BigIntField(primary_key=True)
    asin = fields.CharField(max_length=10, description="ASIN of the product")
    fnsku = fields.CharField(max_length=13, description="FNSKU of the product")
    sku = fields.CharField(max_length=30, description="SKU of the product")
    seller_sku = fields.CharField(max_length=30, description="Seller SKU of the product")
    listing_id = fields.CharField(max_length=15, description="Listing ID of the product")
    code = fields.CharField(max_length=32,  null=True, description="Transparency code")
    hash = fields.CharField(max_length=32,  description="MD5 of the code")
    filename = fields.CharField(max_length=255, description="Name of the file")
    batch_id = fields.CharField(max_length=25,  description="Batch ID")
    page = fields.IntField(min=1, max=9999, description="Page number of the code in the batch")
    total = fields.IntField(description="Total number of codes in the batch")
    created_at = fields.DatetimeField(auto_now_add=True, null=True, description="Creation date")
    created_by = fields.CharField(max_length=20, null=True, description="User who created the code")
    updated_at = fields.DatetimeField(null=True, description="Last update date")
    updated_by = fields.CharField(max_length=20, null=True, description="User who updated the code")
    status = fields.IntEnumField(TransparencyCodeStatus, default=TransparencyCodeStatus.UNUSED, description="Status of the code")

    class Meta:
        table = "transparency_code"
        ordering = ["batch_id", "page"]

TransparencyCode_Pydantic = pydantic_model_creator(TransparencyCodeModel, name="TransparencyCode")

class ActionType(IntEnum):
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4
    CALCULATE = 5

class TransparencyCodePrintLogModel(models.Model):
    id = fields.BigIntField(primary_key=True)
    batch_id = fields.CharField(max_length=25,  description="Batch ID")
    listing_id = fields.CharField(max_length=15, description="Listing ID of the product")
    seller_sku = fields.CharField(max_length=30, description="Seller SKU of the product")
    action = fields.IntEnumField(ActionType, description="Action performed on the code")
    charged = fields.IntField(description="Number of codes charged")
    status = fields.IntEnumField(TransparencyCodeStatus, description="Status of the code")
    created_at = fields.DatetimeField(auto_now_add=True, description="Creation date")
    created_by = fields.CharField(max_length=20, description="User who created the log")
    content = fields.CharField(max_length=200, description="Content of the log")

    class Meta:
        table = "transparency_code_print_log"
        ordering = ["-created_at"]

TransparencyCodePrintLog_Pydantic = pydantic_model_creator(TransparencyCodePrintLogModel, name="TransparencyCodePrintLog")


