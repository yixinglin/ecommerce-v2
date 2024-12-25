from pydantic import BaseModel, Field


class Seller(BaseModel):
    sid: int
    name: str
    account_name: str
    marketplace_id: str
    status: bool = Field(default=False)
    country: str
    region: str

class Marketplace(BaseModel):
    mid: int
    region: str
    aws_region: str
    country: str
    code: str
    marketplace_id: str

class Inventory(BaseModel):
    sku: str
    quantity: int
    warehouse_id: int = Field(default=0)
    warehouse_name: str = Field(default='')
    storage_location: str = Field(default='')


class Listing(BaseModel):
    listing_id: str
    sid: int
    seller_sku: str
    fnsku: str
    item_name: str
    asin: str
    parent_asin: str
    small_image_url: str
    status: bool = Field(default=False)
    is_delete: bool = Field(default=False)
    local_sku: str
    local_name: str
    price: float
    currency_code: str
    fulfillment_channel_type: str
    label: str = Field(default='')

class FbaShipmentPlan(BaseModel):
    seq: str = Field(description="Sequence number")
    order_sn: str = Field(description="Order serial number")
    sid: int = Field(description="Seller ID")
    create_time: str = Field(default='', description="Creation time")
    create_user: str = Field(default='', description="Creation user")
    fnsku: str = Field(default='', description="FN SKU")
    msku: str = Field(default='', description="MSKU")
    wname: str = Field(default='', description="Warehouse name")
    status: int
    status_name: str = Field(default='', description="Status name")
    shipment_time: str = Field(default='', description="Shipment time")
    shipment_plan_quantity: int = Field(description="Shipment plan quantity")
    quantity_in_case: int = Field(description="Quantity in case")
    box_num: int = Field(description="Box number")
    small_image_url: str = Field(default='', description="Small image URL")
    product_name: str = Field(description="Product name")
    sku: str = Field(default='', description="SKU")
    is_combo: bool = Field(default=False, description="Whether the product is a combo")
    is_urgent: bool = Field(default=False, description="Whether the product is urgent")

class PrintShopListingVO(BaseModel):
    listing_id: str = Field(default='', description="Listing ID")
    seller_sku: str = Field(default='', description="Seller SKU")
    fnsku: str = Field(default='', description="FN SKU")
    item_name: str = Field(default='', description="Product name")
    asin: str = Field(default='', description="ASIN")
    parent_asin: str = Field(default='', description="Parent ASIN")
    small_image_url: str = Field(default='', description="Small image URL")
    status: bool = Field(default=False, description="Product status, 0: off sale, 1: on sale")
    is_delete: bool = Field(default=False, description="Whether the product is deleted, 0: not deleted, 1: deleted")
    local_sku: str = Field(default='', description="Local sku in ERP system")
    local_name: str = Field(default='', description="Local name in ERP system")
    price: float = Field(default=0.0, description="Product price")
    currency_code: str = Field(default='', description="Currency code")
    fulfillment_channel_type: str = Field(default='', description="Fulfillment channel type")

    seller: Seller = Field(default=None, description="Seller information")
    inventories: list[Inventory] = Field(default=[], description="Inventory information")

class PrintShopFbaShipmentPlanVO(FbaShipmentPlan):
    seller: Seller = Field(default=None, description="Seller information")
    inventories: list[Inventory] = Field(default=[], description="Inventory information")
