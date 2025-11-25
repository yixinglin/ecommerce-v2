import datetime
from typing import Optional

from fastapi import Query
from pydantic import BaseModel

from . import CarrierCode
from .common.enums import IntegrationType
from .models import OrderStatus, ChannelCode

class PullOrdersRequest(BaseModel):
    channel_code: str
    account_id: str

class OrderQueryRequest(BaseModel):
    status: Optional[OrderStatus] = Query(None, description="Order status")
    channel_code: Optional[ChannelCode] = Query(None, description="Channel code, e.g. Woocommerce")
    keyword: Optional[str] = Query(None, description="Keyword to search for order")
    delivered: Optional[bool] = Query(None, description="Filter by delivered orders")
    created_from: Optional[datetime.datetime] = Query(None, description="Created from date")
    page: int = Query(1, ge=1, description="Page number")
    limit: int = Query(10, ge=1, description="Page size")

class OrderUpdateRequest(BaseModel):
    status: Optional[OrderStatus] = Query(None, description="Order status")
    carrier_code: Optional[CarrierCode] = Query(None, description="Carrier code")
    parcel_weights: Optional[str] = Query(None, description="Parcel weights")
    tracking_number: Optional[str] = Query(None, description="Tracking number")
    tracking_url: Optional[str] = Query(None, description="Tracking URL")
    delivered: Optional[bool] = Query(None, description="Is delivered or not")
    seller_note: Optional[str] = Query(None, description="Seller note")
    estimated_delivery_date: Optional[datetime.date] = Query(None, description="Estimated delivery date")

class OrderResponse(BaseModel):
    id: int
    order_number: Optional[str]
    channel: Optional[str]
    account_id: Optional[str]
    status: OrderStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    shipping_address_id: Optional[int]
    billing_address_id: Optional[int]
    buyer_name: Optional[str]
    buyer_address: Optional[str]
    country_code:  Optional[str]

    customer_note: Optional[str]
    seller_note: Optional[str]
    estimated_delivery_date: Optional[datetime.date]

    tracking_number: Optional[str]
    tracking_url: Optional[str]
    tracking_info: Optional[str]
    carrier_code: Optional[CarrierCode]

    thumbnails: Optional[str]
    delivered: Optional[bool]

    parcel_weights: Optional[str]

    label_retry_count: Optional[int]
    sync_retry_count: Optional[int]

    batch_id: Optional[str]

class OrderItemResponse(BaseModel):
    id: int
    item_number: str
    order_id: int
    name: str
    sku: str
    quantity: int
    unit_price_excl_tax: float
    subtotal_excl_tax: float
    total_incl_tax: float
    tax_rate_percent: float
    weight: float
    height: float
    width: float
    length: float
    image_url: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

class CreateBatchRequest(BaseModel):
    channel_code: ChannelCode = Query(..., description="Channel code, e.g. Woocommerce")
    account_id: Optional[str] = Query(None, description="Account ID")
    operator: Optional[str] = Query("system", description="Operator name")


class AddressUpdateRequest(BaseModel):
    name: Optional[str] = Query(None, description="Name of the address")
    company: Optional[str] = Query(None, description="Company name")
    address1: Optional[str] = Query(None, description="Address line 1")
    address2: Optional[str] = Query(None, description="Address line 2")
    city: Optional[str] = Query(None, description="City")
    state_or_province: Optional[str] = Query(None, description="State or province")
    postal_code: Optional[str] = Query(None, description="Postal code")
    country_code: Optional[str] = Query(None, description="Country code")

class ShippingTrackingResponse(BaseModel):
    order_id: Optional[int]
    tracking_number: Optional[str]
    carrier_code: Optional[CarrierCode]
    location: Optional[str]
    country_code: Optional[str]
    description: Optional[str]
    status_text: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class IntegrationCredentialResponse(BaseModel):
    id: int
    name: str
    type: IntegrationType
    provider_code: str
    external_id: str
    expires_at: Optional[datetime.datetime]
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

class IntegrationCredentialUpdateRequest(BaseModel):
    name: Optional[str] = Query(None, description="Name of the integration")
    is_active: Optional[bool] = Query(None, description="Is active or not")
    expires_at: Optional[datetime.datetime] = Query(None, description="Expiry date of the integration")