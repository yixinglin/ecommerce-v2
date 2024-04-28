from typing import List
from pydantic import BaseModel


class Product(BaseModel):
    productId: int
    ean: str
    count: int
    picture: str
    url: str
    title: str


class DailySalesCountVO(BaseModel):
    products: List[Product]
    createdDate: str
    status: str
