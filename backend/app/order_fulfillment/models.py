from decimal import Decimal

from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from .common.enums import *
from models.base import TortoiseBasicModel

class OrderModel(TortoiseBasicModel):
    id = fields.BigIntField(pk=True)
    order_number = fields.CharField(max_length=64, description="Unique order ID from the channel")
    channel = fields.CharEnumField(ChannelCode, max_length=32, description="Sales channel (e.g., shopify, jd, tmall)")
    account_id = fields.CharField(max_length=64, null=True, description="External account ID (shop ID, etc.)")

    # 本地的订单处理状态
    status = fields.CharEnumField(OrderStatus, max_length=32, default=OrderStatus.NEW, description="Order processing status")

    shipping_address_id = fields.BigIntField(null=True, description="Reference to shipping address ID")
    billing_address_id = fields.BigIntField(description="Reference to billing address ID")

    customer_note = fields.CharField(max_length=255, null=True, description="Customer note (e.g., special request, etc.)")

    # 冗余字段
    buyer_name = fields.CharField(max_length=64, null=True, description="Redundant field for buyer's name")
    buyer_address = fields.CharField(max_length=255, null=True, description="Redundant field for buyer address")
    country_code = fields.CharField(max_length=4, null=True, description="Redundant field for ISO country code (e.g., US, CN)")
    # 冗余字段
    tracking_number = fields.CharField(max_length=255, null=True, description="Generated logistics tracking number")
    tracking_url = fields.CharField(max_length=255, null=True, description="Logistics tracking URL")
    carrier_code = fields.CharEnumField(CarrierCode, max_length=32, null=True, description="Logistics provider code (e.g., SF, UPS)")
    # 冗余字段
    thumbnails = fields.TextField(null=True, description="Thumbnail URLs of the order")

    label_retry_count = fields.IntField(default=0, description="Retry count for shipping label generation")
    sync_retry_count = fields.IntField(default=0, description="Retry count for syncing to platform")
    printshop_retry_count = fields.IntField(default=0, description="Retry count for printshop upload")

    batch_id = fields.CharField(max_length=64, null=True, description="Batch number after sync to platform")
    sort_key = fields.CharField(max_length=64, null=True, description="Sort key for sorting orders in a batch")

    synced_at = fields.DatetimeField(null=True, description="Time when tracking info was synced to platform")
    uploaded_at = fields.DatetimeField(null=True, description="Time when order was uploaded to printshop")
    completed_at = fields.DatetimeField(null=True, description="Time when order was fully processed")

    raw_data = fields.JSONField(null=True, description="Original raw order data from the channel")

    class Meta:
        table = "ofa_orders"
        unique_together = [("channel", "account_id", "order_number")]

OrderModel_Pydantic = pydantic_model_creator(OrderModel, name="OrderModel")


class OrderItemModel(TortoiseBasicModel):
    id = fields.BigIntField(pk=True)
    item_number = fields.CharField(max_length=64, null=True, description="Unique item ID from the channel")
    order_id = fields.BigIntField(description="Reference to order ID")
    name = fields.CharField(max_length=255, description="Product name")
    sku = fields.CharField(max_length=64, description="Product SKU or item number")
    quantity = fields.IntField(default=1, description="Quantity of this item")
    unit_price_excl_tax = fields.DecimalField(default=Decimal("0.00"), max_digits=10, decimal_places=2, description="Item price (unit price)")
    subtotal_excl_tax = fields.DecimalField(default=Decimal("0.00"), max_digits=10, decimal_places=2, description="Subtotal of this item")
    total_incl_tax = fields.DecimalField(default=Decimal("0.00"), max_digits=10, decimal_places=2, description="Total price of this item")
    tax_rate_percent = fields.DecimalField(default=19, max_digits=5, decimal_places=2, null=True, description="Tax rate percentage, e.g. 19.00 for 19%")
    image_url = fields.CharField(max_length=255, null=True, description="Product image URL")
    weight = fields.DecimalField(default=Decimal("0.00"), max_digits=10, decimal_places=2, null=True, description="Product weight (in kg)")
    length = fields.DecimalField(default=Decimal("0.00"), max_digits=10, decimal_places=2, null=True, description="Product length (in cm)")
    width = fields.DecimalField(default=Decimal("0.00"), max_digits=10, decimal_places=2, null=True, description="Product width (in cm)")
    height = fields.DecimalField(default=Decimal("0.00"), max_digits=10, decimal_places=2, null=True, description="Product height (in cm)")
    raw_data = fields.JSONField(null=True, description="Original raw item data from the channel")

    class Meta:
        table = "ofa_order_items"

OrderItemModel_Pydantic = pydantic_model_creator(OrderItemModel, name="OrderItemModel")

class AddressModel(TortoiseBasicModel):
    id = fields.BigIntField(pk=True)

    name = fields.CharField(max_length=128, description="Full name of recipient or payer")
    company = fields.CharField(max_length=128, null=True, description="Company name (optional)")
    phone = fields.CharField(max_length=32, null=True, description="Phone number")
    mobile = fields.CharField(max_length=32, null=True, description="Mobile phone number")
    email = fields.CharField(max_length=128, null=True, description="Email address")

    address1 = fields.CharField(max_length=255, description="Primary street address")
    address2 = fields.CharField(max_length=255, null=True, description="Secondary address line (apt, suite, etc.)")
    city = fields.CharField(max_length=128, description="City name")
    state_or_province = fields.CharField(max_length=128, null=True, description="State or province name")
    postal_code = fields.CharField(max_length=32, description="Postal or ZIP code")
    country = fields.CharField(max_length=64, description="Country name")
    country_code = fields.CharField(max_length=8, description="ISO country code (e.g., US, CN)")

    address_type = fields.CharEnumField(AddressType, max_length=10, description="Address type: shipping or billing")

    class Meta:
        table = "ofa_addresses"
        table_description = "Shipping or billing address table"

AddressModel_Pydantic = pydantic_model_creator(AddressModel, name="AddressModel")

class OrderBatchModel(TortoiseBasicModel):
    id = fields.BigIntField(pk=True)
    batch_id = fields.CharField(unique=True, max_length=64, description="Unique batch ID")
    order_count = fields.IntField(default=0, description="Number of orders in this batch")
    download_count = fields.IntField(default=0, description="Number of times this batch was downloaded")
    status = fields.CharEnumField(
        OrderBatchStatus,
        max_length=32,
        default=OrderBatchStatus.PENDING,
        description="Batch processing status"
    )
    operator = fields.CharField(max_length=64, null=True, description="Operator who triggered upload")

    class Meta:
        table = "ofa_order_batches"
        table_description = "Order batch metadata for platform sync and printshop upload"

OrderBatchModel_Pydantic = pydantic_model_creator(OrderBatchModel, name="OrderBatchModel")

class OrderStatusLogModel(TortoiseBasicModel):
    id = fields.BigIntField(pk=True)
    # order_id = fields.CharField(max_length=64, description="Order ID related to this status change")
    order_id = fields.BigIntField(description="Associated order ID")
    channel = fields.CharEnumField(ChannelCode, max_length=32, description="Channel of the order")

    from_status = fields.CharEnumField(OrderStatus, max_length=32, null=True, description="Previous order status")
    to_status = fields.CharEnumField(OrderStatus, max_length=32, description="New order status")
    # changed_by = fields.CharField(max_length=64, default="system", description="Who changed the status")
    remarks = fields.TextField(null=True, description="Optional comment or reason")

    # changed_at = fields.DatetimeField(auto_now_add=True, description="Status change timestamp")

    class Meta:
        table = "ofa_order_status_logs"
        table_description = "Order status transition history"

OrderStatusLogModel_Pydantic = pydantic_model_creator(OrderStatusLogModel, name="OrderStatusLogModel")

class OrderErrorLogModel(TortoiseBasicModel):
    id = fields.BigIntField(pk=True)
    # order_id = fields.CharField(max_length=64, description="Order ID associated with this error")
    order_id = fields.BigIntField(description="Associated order ID")
    channel = fields.CharEnumField(ChannelCode, max_length=32, description="Sales channel of the order")

    operation = fields.CharEnumField(OperationType, max_length=16, description="Operation name: label_gen / sync / upload")
    error_code = fields.CharField(max_length=32, null=True, description="Error code or type")
    error_message = fields.TextField(description="Full error message or stack trace")
    retry_count = fields.IntField(default=0, description="Number of retries attempted for this operation")

    class Meta:
        table = "ofa_order_errors"
        table_description = "Detailed error logs for order processing failures"


OrderErrorLogModel_Pydantic = pydantic_model_creator(OrderErrorLogModel, name="OrderErrorLogModel")


class ShippingLabelModel(TortoiseBasicModel):
    id = fields.BigIntField(pk=True)
    # order_id = fields.CharField(max_length=64, description="Associated order ID")
    order_id = fields.BigIntField(description="Associated order ID")
    channel = fields.CharField(max_length=32, description="Order source channel")
    external_id = fields.CharField(max_length=64, null=True, description="Account ID of the logistics provider")

    tracking_number = fields.CharField(max_length=32, description="Logistics tracking number")
    tracking_id = fields.CharField(max_length=32, null=True, description="Logistics tracking ID")
    tracking_url = fields.CharField(max_length=255, null=True, description="Tracking url")
    carrier_code = fields.CharField(max_length=32, description="Carrier code (e.g., SF, UPS)")
    label_file_base64 = fields.TextField(description="Base64 encoded label PDF/image")

    class Meta:
        table = "ofa_shipping_labels"
        table_description = "Optional table for storing multi-package shipping labels"

ShippingLabelModel_Pydantic = pydantic_model_creator(ShippingLabelModel, name="ShippingLabelModel")


class IntegrationCredentialModel(models.Model):
    id = fields.BigIntField(pk=True)

    name = fields.CharField(max_length=64, description="Optional display name for this credential")
    type = fields.CharEnumField(IntegrationType, max_length=32, description="Integration type: order_channel, logistics, etc.")

    provider_code = fields.CharField(max_length=64, description="Provider code: e.g. shopify, dhl")
    external_id = fields.CharField(max_length=128, null=True, description="External shop ID or account ID")

    # API auth fields
    api_key = fields.CharField(max_length=256, null=True, description="API key or token")
    api_secret = fields.CharField(max_length=256, null=True, description="API secret or password")
    access_token = fields.TextField(null=True, description="OAuth access token (if applicable)")
    refresh_token = fields.TextField(null=True, description="OAuth refresh token (if applicable)")
    expires_at = fields.DatetimeField(null=True, description="Token expiration time")

    meta = fields.JSONField(null=True, description="Any extra fields (like base_url, account_id, etc.)")

    is_active = fields.BooleanField(default=True, description="Whether this credential is currently active")

    created_at = fields.DatetimeField(auto_now_add=True, description="Creation time")
    updated_at = fields.DatetimeField(auto_now=True, description="Last updated time")

    class Meta:
        table = "ofa_integration_credentials"
        table_description = "Stores API credentials for order channels, logistics, or third-party providers"
        unique_together = (("type", "provider_code", "external_id"),)

IntegrationCredentialModel_Pydantic = pydantic_model_creator(IntegrationCredentialModel, name="IntegrationCredentialModel")