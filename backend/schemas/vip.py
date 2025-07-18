from typing import Optional

from pydantic import BaseModel, Field
from models import Address


class VipOrderLine(BaseModel):
    quantity: int
    sellerSKU: str
    unit: str
    productName: str
    price: float

class VipOrder(BaseModel):
    orderId: str
    buyerId: Optional[int] = None
    orderLines: list[VipOrderLine] = Field(..., min_items=1)
    shipAddress: Address
