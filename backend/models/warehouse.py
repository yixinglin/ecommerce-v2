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
    inventoryDiffQuantity: int # counted quantity - quantity on hand
    locationName: str
    locationId: str
    locationCode: str
    warehouseId: str
    warehouseName: str
    lastCountDate: str

