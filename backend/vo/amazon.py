from pydantic import BaseModel
from typing import List


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
