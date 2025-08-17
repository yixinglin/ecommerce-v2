from enum import Enum

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


class OrderStatus(str, Enum):
    PENDING = "pending"        # 等待付款
    PROCESSING = "processing"  # 处理中（已付款，待发货）
    ON_HOLD = "on-hold"        # 挂起（等待确认付款）
    COMPLETED = "completed"    # 已完成
    CANCELLED = "cancelled"    # 已取消
    REFUNDED = "refunded"      # 已退款
    FAILED = "failed"          # 失败（付款失败）


class OrderAddressModel(BaseModel):
    """订单地址模型（可用于 billing / shipping）"""
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_1: str
    address_2: Optional[str] = None
    city: str
    postcode: str
    state: Optional[str] = None
    country: str
    address_type: str = Field(..., description="billing 或 shipping")


class OrderLineModel(BaseModel):
    """订单行模型"""
    product_id: int
    name: str
    sku: Optional[str]
    quantity: int
    price: float
    total: float


class OrderModel(BaseModel):
    """订单主模型"""
    order_number: str
    status: str
    date_created: datetime
    date_updated: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    date_paid: Optional[datetime] = None
    currency: str

    shipping_total: float  # Shipping Fee Netto
    subtotal: float   # Subtotal Netto
    total: float     # Total Netto
    payment_method: str
    customer_id: str
    first_sku: str

    billing_address: OrderAddressModel
    shipping_address: OrderAddressModel
    line_items: List[OrderLineModel]


def parse_order(raw: dict) -> OrderModel:
    billing = OrderAddressModel(
        **raw["billing"],
        address_type="billing"
    )

    shipping = OrderAddressModel(
        **raw["shipping"],
        address_type="shipping"
    )

    line_items = [
        OrderLineModel(
            product_id=line["product_id"],
            name=line["name"],
            sku=line.get("sku"),
            quantity=line["quantity"],
            price=float(line["price"]),
            total=float(line["total"])
        )
        for line in raw["line_items"]
    ]

    order = OrderModel(
        order_number=raw["number"],
        status=raw["status"],
        currency=raw["currency"],
        date_created=raw["date_created"],
        date_updated=raw.get("date_modified"),
        date_completed=raw.get("date_completed"),
        date_paid=raw.get("date_paid"),
        shipping_total=float(raw["shipping_total"]),
        total=float(raw["total"]) / 1.19,
        subtotal=(float(raw["total"]) / 1.19) - float(raw["shipping_total"]),
        payment_method=raw["payment_method_title"],
        customer_id=str(raw["customer_id"]),
        first_sku=raw["line_items"][0]["sku"],
        billing_address=billing,
        shipping_address=shipping,
        line_items=line_items
    )
    return order
