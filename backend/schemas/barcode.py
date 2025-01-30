from pydantic import BaseModel


class ProductBasicInfo(BaseModel):
    id: int
    sku: str
    name: str
    barcode: str
    image_url: str
    description: str
    weight: float
    uom: str
    qty_available: int
    active: bool

class ProductFullInfo(ProductBasicInfo):
    pass





class ProductUpdate(BaseModel):
    barcode: str
    image_url: str
    weight: float

class Inventory(BaseModel):
    id: int
    product_id: int
    loc_code: str
    quantity: float
    warehouse_id: int
    warehouse_name: str