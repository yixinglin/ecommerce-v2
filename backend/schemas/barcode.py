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

class ProductPackaging(BaseModel):
    id: int
    product_id: int
    product_name: str
    name: str
    qty: int
    uom: str
    barcode: str

class ProductPackagingUpdate(BaseModel):
    qty: int= Field(None, description="Quantity of the packaging")
    barcode: str= Field(None, description="Barcode of the packaging")
    name: str= Field(None, description="Name of the packaging")

class Quant(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_uom: str
    sku: str
    location_code: str
    quantity: float             # quantity on hand
    reserved_quantity: float
    available_quantity: float   # available quantity
    inventory_quantity: float   # counted quantity
    inventory_quantity_set: bool # whether inventory quantity is set manually or not
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    last_count_days: int
