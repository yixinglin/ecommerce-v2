from typing import List, Union
from pydantic import BaseModel, Field


class Address(BaseModel):
    name1: str
    name2: str
    name3: str
    street1: str
    zipCode: str
    city: str
    province: str = Field(default="", description="Province")
    country: str
    email: str = Field(default="", description="Email address of the address")
    telephone: str = Field(default="", description="Telephone number of the address")
    mobile: str = Field(default="", description="Mobile number of the address")
    fax: str = Field(default="", description="Fax number of the address")


class Parcel(BaseModel):
    trackNumber: str = Field(default="", description="Tracking number of the parcel")
    parcelNumber: str = Field(default="", description="Parcel number of the parcel")
    weight: float = Field(default=1.0, description="Weight of the parcel in kg")  # in kg
    width: float = Field(default=0.0, description="Width of the parcel in cm")  # in cm
    height: float = Field(default=0.0, description="Height of the parcel in cm")  # in cm
    length: float = Field(default=0.0, description="Length of the parcel in cm")  # in cm
    comment: str = Field(default="", description="Additional information about the parcel")
    content: str = Field(default="", description="Content of the parcel")
    value: float = Field(default=0.0, description="Value of the parcel in EUR")  # in EUR

    @classmethod
    def default(cls):
        return cls(weight=1.0, width=0.0, height=0.0, length=0.0, comment="", content="", value=0.0)


class StandardShipment(BaseModel):
    shipper: Union[Address, None] = Field(default=None, description="Address of the shipper")
    consignee: Union[Address, None] = Field(default=None, description="Address of the consignee")
    parcels: List[Parcel]
    references: List[str]
    location: str = Field(default="", description="Location of the parcels")


def create_shipment_example():
    # Create a German address
    consignee_address = Address(
        name1="Max Mustermann",
        name2="Auf Luft Production Kommunikationsmarketing GmbH",
        name3="UG",
        street1="Musterstraße 123",
        zipCode="12345",
        city="Berlin",
        province="Berlin",
        country="DE",
        email="max.mustermann@example.com",
        telephone="+49 123 456789",
        mobile="+49 987 654321",
        fax=""
    )

    # Create a shipper address
    shipper_address = Address(
        name1="John Doe",
        name2="",
        name3="",
        street1="Main Street 123",
        zipCode="12345",
        city="Hamburg",
        province="",
        country="Deutschland",
        email="john.doe@example.com",
        telephone="+1 234 567 8901",
        mobile="+1 987 654 3210",
        fax=""
    )

    # Create a Parcel instance
    parcel = Parcel(
        trackNumber="ABC123456789",
        parcelNumber="P123456789",
        weight=1.5,
        width=20.0,
        height=15.0,
        length=30.0,
        comment="Fragile",
        content="Electronics",
        value=150.0
    )

    # Create a StandardShipment instance
    shipment = StandardShipment(
        shipper=shipper_address,
        consignee=consignee_address,
        references=["REF1", "REF2"],
        parcels=[parcel]
    )
    return shipment
