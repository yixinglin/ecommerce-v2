from enum import StrEnum

from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from models.base import TortoiseBasicModel


class DataType(StrEnum):
    Any = "any"
    INT = "int"
    STR = "str"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"
    BINARY = "binary"
    HYPERLINK = "hyperlink"
    CURRENCY = "currency"
    TEXT = "text"
    HTML = "html"

class TemplateChannel(StrEnum):
    Amazon = "Amazon"
    Odoo = "Odoo"
    Lingxing = "Lingxing"
    HG_VIP = "HG-VIP"
    HG_24 = "HG-24"
    Kaufland = "Kaufland"
    Metro = "Metro"
    Otto = "Otto"
    Shopify = "Shopify"
    WooCommerce = "WooCommerce"
    Other = "Other"

class TemplateType(StrEnum):
    Product = "Product"
    Offer = "Offer"
    Listing = "Listing"
    Order = "Order"
    OrderItem = "OrderItem"
    Inventory = "Inventory"
    Customer = "Customer"
    Any = "Any"

class TemplateModel(TortoiseBasicModel):
    """
    Table: tc_template
    Stores metadata for source/target templates.
    """
    id = fields.IntField(pk=True, description="Primary key: Template ID")
    name = fields.CharField(
        max_length=25,
        unique=True,
        description="Template name, e.g. Amazon-Product-Template"
    )
    remark = fields.CharField(max_length=250, null=True, description="Optional remark")
    channel = fields.CharField(enum_type=TemplateChannel, max_length=25, description="Template channel (e.g. Amazon, Shopify, Lazada, WooCommerce, Etsy)")
    type = fields.CharField(enum_type=TemplateType, max_length=25, description="Template type (e.g. Product, Offer, Listing, Order, OrderItem, Inventory, Customer, Other)")
    class Meta:
        table = "tc_template"

Template_Pydantic = pydantic_model_creator(TemplateModel, name="Template")

class TemplateFieldModel(TortoiseBasicModel):
    """
    Table: tc_template_field
    Stores individual fields for a specific template.
    """
    id = fields.IntField(pk=True, description="Primary key: Field ID")
    template_id = fields.IntField(description="Reference to template ID")
    field_name = fields.CharField(max_length=25, description="Field name (e.g. ProductName)")
    type = fields.CharField(max_length=16, description="Field data type (e.g. str, int, float, bool, date, datetime, json, uuid, binary)")
    display_name = fields.CharField(max_length=25, null=True, description="Optional display name")
    formula = fields.CharField(max_length=512, null=True, description="Optional formula to calculate field value")
    order_index = fields.IntField(default=0, description="Display order index")

    class Meta:
        table = "tc_template_field"

TemplateField_Pydantic = pydantic_model_creator(TemplateFieldModel, name="TemplateField")

class MappingModel(TortoiseBasicModel):
    """
    Table: tc_mapping
    Stores one mapping relationship between a source and a target template.
    """
    id = fields.IntField(pk=True, description="Primary key: Mapping ID")
    source_template_id = fields.IntField(description="Source template ID")
    target_template_id = fields.IntField(description="Target template ID")
    name = fields.CharField(max_length=25, description="Mapping name (e.g. Amazon-to-Shopify)")
    remark = fields.CharField(max_length=250, null=True, description="Optional remark")

    class Meta:
        table = "tc_mapping"
        unique_together = (("source_template_id", "target_template_id"),)

Mapping_Pydantic = pydantic_model_creator(MappingModel, name="Mapping")


class MappingPairModel(TortoiseBasicModel):
    """
    Table: tc_mapping_pair
    Stores individual field-to-field mappings under a mapping.
    """
    id = fields.IntField(pk=True, description="Primary key: Mapping pair ID")
    mapping_id = fields.IntField(description="Mapping ID")
    source_field_id = fields.IntField(description="Source field ID")
    target_field_id = fields.IntField(description="Target field ID")

    class Meta:
        table = "tc_mapping_pair"


MappingPair_Pydantic = pydantic_model_creator(MappingPairModel, name="MappingPair")

class ConversionLogModel(TortoiseBasicModel):
    """
    Table: tc_conversion_log
    Logs each conversion request with result status.
    """
    id = fields.IntField(pk=True, description="Primary key: Conversion log ID")
    source_file_name = fields.CharField(max_length=120, description="Original uploaded file name")
    source_template_name = fields.CharField(max_length=25, description="Source template name")
    target_template_name = fields.CharField(max_length=25, description="Target template name")
    message = fields.CharField(max_length=255, null=True, description="Optional message")

    class Meta:
        table = "tc_conversion_log"

ConversionLog_Pydantic = pydantic_model_creator(ConversionLogModel, name="ConversionLog")