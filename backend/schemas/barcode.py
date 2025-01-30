from pydantic import BaseModel, Field


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
    barcode: str= Field(None, description="Barcode of the product")
    b64_image: str= Field(None, description="Base64 encoded image of the product")
    weight: float= Field(None, description="Weight of the product")

class Inventory(BaseModel):
    id: int
    product_id: int
    loc_code: str
    quantity: float
    warehouse_id: int
    warehouse_name: str