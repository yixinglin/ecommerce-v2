from enum import Enum
from typing import List, Union

from pydantic import BaseModel, Field
from .shipment import Address

class OrderStatus(str, Enum):
    pending = "pending" # An order has been created, but payment has not been made or payment has not been confirmed. This status indicates that the order is awaiting further processing.
    confirmed = "confirmed" # Payment has been confirmed and the order is ready for processing.
    processing = "processing" # Order is being processed and items may be packed or ready to ship. This status indicates that the merchant has begun processing the order.
    partially_shipped = "partially_shipped" # The order has been partially shipped, but not all items have left the warehouse. This status indicates that some items have been shipped but not all.
    shipped = "shipped" #  The order has been shipped and the item has left the warehouse and is in transit. This status indicates that the item has been handed over to a logistics company for transportation.
    out_for_delivery = "out_for_delivery" # The order has arrived at the local distribution center and is being dispatched. This status indicates that the item is about to be delivered to the customer.
    delivered = "delivered" # The order has been successfully delivered to the customer. This status indicates that the order has been processed and the customer has received the item.
    cancelled = "cancelled" # The order has been canceled, possibly by the customer or merchant. This status indicates that the order will no longer be processed.
    returned = "returned" # The ordered item has been returned to the merchant and may be returned by the customer for various reasons. This status indicates that the item has been returned to the merchant, usually accompanied by a refund process.
    refunded = "refunded" # The order has been refunded and the refund has been processed and returned to the customer. This status indicates that the refund process is complete and the customer has received the payment.
    failed = "failed"  # There was an issue during order processing that prevented the order from being completed. This status indicates that the order was not successfully completed and may need to be reprocessed or customer support contacted.
    unknown = "unknown" # The status of the order is not known. This status indicates that the order has not been processed and the status is not known.
    

class OrderItem(BaseModel):
    id: str = Field(description="Unique identifier for the item")
    name: str = Field(description="Name of the item")
    sku: str = Field(description="Unique identifier for the item")
    quantity: int = Field(description="Quantity of the item")
    unit_price: float = Field(default=0, description="Price of the item per unit")
    subtotal: float = Field(default=0, description="Total price of the item")
    tax: float = Field(default=0, description="Tax amount for the item")
    total: float = Field(default=0, description="Total price of the item including tax")
    description: str = Field(default="", description="Description of the item")
    image: str = Field(default="", description="URL of the item image")

class StandardOrder(BaseModel):
    orderId: str = Field(description="Unique identifier for the order")
    sellerId: Union[str, None] = Field(default=None, description="Unique identifier for the seller")
    salesChannel: Union[str, None] = Field(default=None, description="Sales channel used to place the order")
    createdAt: Union[str, None] = Field(default=None, description="Date and time when the order was created")
    updatedAt: Union[str, None] = Field(default=None, description="Date and time when the order was last updated")
    purchasedAt: Union[str, None] = Field(default=None, description="Date and time when the order was purchased")
    status: Union[str, None] = Field(default=None, description="Status of the order")
    shipAddress: Union[Address, None] = Field(default=None, description="Address of the consignee")
    billAddress: Union[Address, None] = Field(default=None, description="Address of the customer")
    items: list[OrderItem] = Field(default=None, description="List of items in the order")
    trackIds: List[str] = Field(default=[""], description="List of tracking IDs for the order")
    parcelNumbers: List[str] = Field(default=[""], description="List of parcel numbers for the order")




