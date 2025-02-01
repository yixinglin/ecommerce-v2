from pydantic import BaseModel


class Quant(BaseModel):
    id: str
    productId: str
    productName: str
    productUom: str
    sku: str
    quantity: int
    reservedQuantity: int
    availableQuantity: int
    locationName: str
    locationId: str
    locationCode: str
    warehouseId: str
    warehouseName: str
    lastCountDate: str

