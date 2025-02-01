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

class Quant(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_uom: str
    sku: str
    location_code: str
    quantity: float
    reserved_quantity: float
    available_quantity: float
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    last_count_date: str
