from pydantic import BaseModel


class Quant(BaseModel):
    id: str
    productName: str
    quantity: int
    reservedQuantity: int
    availableQuantity: int
    sku: str
    unit: str
    locationName: str
    warehouseName: str

