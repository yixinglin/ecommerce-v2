from typing import Optional, List

from pydantic import BaseModel, Field
from models import Address

# ------------VIP系统插件
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


# -------------PIM系统插件----------------


class SpuProduct(BaseModel):
    spuId: int
    spuCode: str
    spuName: str
    spuType: str
    description: Optional[str] = ""
    images: Optional[str] = None
    leadTime: Optional[int] = 7
    hsCode: Optional[str] = None
    pzn: Optional[str] = None

class SkuProduct(BaseModel):
    skuId: int
    skuCode: str
    skuCodeOrigin: str
    skuName: str
    cost: Optional[float] = 0.0
    price: Optional[float] = 0.0
    priceClsa: Optional[float] = 0.0
    priceClsb: Optional[float] = 0.0
    priceClsc: Optional[float] = 0.0
    weight: Optional[float] = 0.0
    unit: Optional[str] = "VE"
    dimensionWidth: Optional[float] = 0.0
    dimensionHeight: Optional[float] = 0.0
    dimensionLength: Optional[float] = 0.0
    packCode: Optional[str] = ""
    cartonQuantity: Optional[int] = 1
    cartonCode: Optional[str] = ""
    palletQuantity: Optional[int] = 1
    palletCode: Optional[str] = ""
    showStatus: Optional[int]

class PimProduct(BaseModel):
    spu: SpuProduct
    skuList: List[SkuProduct]


# ----------CRM系统插件--------------

class CrmAddress(BaseModel):
    name: Optional[str]
    name2: Optional[str] = None
    code: Optional[str] = None
    street: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None
    telefon: Optional[str] = None
    mobil: Optional[str] = None
    email: Optional[str] = None
    webseite: Optional[str] = None
    memo: Optional[str] = None
    type: Optional[str] = None
    groupAlt: Optional[str] = None
    vipUsername: Optional[str] = None
    vipPassword: Optional[str] = None

class CrmContact(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str]
    telefon: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    positionText: Optional[str] = None
    type: Optional[str] = None
    salutation: Optional[str] = None  # Frau, Herr, etc.

class CrmAddressProfile(BaseModel):
    pass
