from pydantic import BaseModel
from typing import List


class DailyShipment(BaseModel):
    asin: str
    sellerSKU: str
    totalQuantityShipped: int
    totalQuantityOrdered: int
    title: str


class DailySalesCountVO(BaseModel):
    """
    This class represents the daily sales count VO.
    """
    purchaseDate: str
    dailyShipments: List[DailyShipment]
