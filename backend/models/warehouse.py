from pydantic import BaseModel


class Quant(BaseModel):
    id: str
    productId: str
    productName: str
    productUom: str
    sku: str
    quantity: int   # quantity on hand
    reservedQuantity: int
    availableQuantity: int # available quantity
    inventoryQuantity: int # counted quantity
    inventoryQuantitySet: bool # whether inventory quantity is set or not
    locationName: str
    locationId: str
    locationCode: str
    warehouseId: str
    warehouseName: str
    lastCountDate: str

class PutawayRule(BaseModel):
    id: str
    productId: str
    productName: str
    locationInId: str
    locationInName: str
    locationInCode: str
    locationOutId: str
    locationOutName: str
    locationOutCode: str
    active: bool
    priority: int
    company: str
