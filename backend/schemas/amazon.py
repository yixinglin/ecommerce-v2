from pydantic import BaseModel, Field
from typing import List, Union

from models.orders import OrderItem, StandardOrder

"""
    These classes represent the models that display the daily sales count to users.
"""

class DailyShipment(BaseModel):
    asin: str
    sellerSKU: str
    totalQuantityShipped: int
    totalQuantityOrdered: int
    title: str
    imageUrl: str = None


class DailySalesCountVO(BaseModel):
    """
    This class represents the daily sales count VO.
    """
    purchaseDate: str
    hasUnshippedOrderItems: bool   # 1 if there are unshipped order items, 0 otherwise
    dailyShippedItemsCount: int  # total number of items shipped on the purchase date
    dailyOrdersItemsCount: int # total number of items ordered on the purchase date
    dailyShipments: List[DailyShipment]


"""
These classes represent the models used to post the data to the api endpoint.
"""
class PackSlipRequestBody(BaseModel):
    country: str = Field(default='DE', description="Request body for the pack slip endpoint. e.g. DE, FR, ES, etc.")
    formatIn: str = Field(description="Format of the input data. Currently only 'html' is supported.")
    data: str = Field(description="The data to be converted to pack slip format.")
    formatOut: str = Field(default=None, description="Format of the output data. e.g. csv, json, etc.")

# class AmazonOrderItem(OrderItem):
#     isTransparency: bool = Field(default=False, description="True if the item is transparent, False otherwise.")
#
# class AmazonStandardOrder(StandardOrder):
#     items: Union[List[AmazonOrderItem], None] =  Field(default=None, description="List of order items.")


class PackageDimensions(BaseModel):
    length: float = Field(description="Length of the package in mm.")
    width: float = Field(description="Width of the package in mm.")
    height: float = Field(description="Height of the package in mm.")
    weight: float = Field(description="Weight of the package in g.")

class CatalogAttributes(BaseModel):
    asin: str = Field(description="Amazon Standard Identification Number (ASIN) of the item.")
    seller_sku: str = Field(description="Seller SKU of the item.")
    brand: str = Field(description="Brand of the item.")
    title: str = Field(description="Title of the item.")
    image_url: str = Field(default=None, description="URL of the item image.")
    package_dimensions: PackageDimensions = Field(description="Dimensions of the package.")

class FnskuLabel(BaseModel):
    fnsku: str = Field(description="The unique identifier of the item.")
    seller_sku: str = Field(description="Seller SKU of the item.")
    title: str = Field(description="Title of the item.")
    note: str = Field(default=None, description="Additional information about the item.")
