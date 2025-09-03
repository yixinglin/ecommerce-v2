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

class VipCustomer(BaseModel):
    companyName: str
    contact: Optional[str] = None
    address: str
    addressLine2: Optional[str] = None
    email: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None


