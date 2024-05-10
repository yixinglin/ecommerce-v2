from typing import List
from pydantic import BaseModel


class Address(BaseModel):
    name1: str
    name2: str
    name3: str
    street1: str
    zipCode: str
    city: str
    province: str
    country: str
    email: str
    telephone: str
    mobile: str
    fax: str


class Parcel(BaseModel):
    weight: float  # in kg
    width: float  # in cm
    height: float  # in cm
    length: float  # in cm
    comment: str
    content: str
    value: float  # in EUR

    @classmethod
    def default(cls):
        return cls(weight=1.0, width=0.0, height=0.0, length=0.0, comment="", content="", value=0.0)


class StandardShipment(BaseModel):
    shipperId: str
    references: List[str]
    address: Address
    parcels: List[Parcel]
