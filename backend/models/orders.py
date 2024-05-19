from typing import List

from pydantic import BaseModel, Field
from .shipment import Address

class OrderItem(BaseModel):
    id: str = Field(description="Unique identifier for the item")
    name: str = Field(description="Name of the item")
    sku: str = Field(description="Unique identifier for the item")
    quantity: int = Field(description="Quantity of the item")
    unit_price: float = Field(description="Price of the item per unit")
    subtotal: float = Field(description="Total price of the item")
    tax: float = Field(description="Tax amount for the item")
    total: float = Field(description="Total price of the item including tax")
    description: str = Field(description="Description of the item")
    image: str = Field(description="URL of the item image")

class StandardOrder(BaseModel):
    orderId: str = Field(description="Unique identifier for the order")
    sellerId: str = Field(description="Unique identifier for the seller")
    salesChannel: str = Field(description="Sales channel used to place the order")
    createdAt: str = Field(description="Date and time when the order was created")
    updatedAt: str = Field(description="Date and time when the order was last updated")
    purchasedAt: str = Field(description="Date and time when the order was purchased")
    status: str = Field(description="Status of the order")
    shipAddress: Address = Field(description="Address of the consignee")
    billAddress: Address = Field(description="Address of the customer")
    items: list[OrderItem] = Field(description="List of items in the order")
    trackIds: List[str] = Field(default=[""], description="List of tracking IDs for the order")
    parcelNumbers: List[str] = Field(default=[""], description="List of parcel numbers for the order")




