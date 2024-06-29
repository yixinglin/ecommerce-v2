from enum import Enum
from typing import List, Union
from pydantic import BaseModel, Field


class ShipmentStatus(str, Enum):
    Preadvice = "PREADVICE"  # "Preadvice: Data has been electronically created. Parcel not yet handed over to Carrier."
    Cancelled = "CANCELLED"  # "Cancelled: Pickup order for the parcel has been cancelled."
    In_Transit = "IN_TRANSIT"  # "In Transit: Parcel has been handed over to Carrier and is being routed."
    Final_Parcel_Center = 'FINAL_PARCEL_CENTER'  # "Final Parcel Center: Parcel has arrived at the final parcel center."
    In_Delivery = 'IN_DELIVERY'  # "In Delivery: Parcel is out for delivery."
    Delivered = 'DELIVERED'  # "Delivered: Parcel has been successfully delivered."
    Not_Delivered = 'NOT_DELIVERED'  # "Not Delivered: Parcel could not be delivered."
    Stored = 'STORED'  # "Stored: Parcel is back at the final parcel center for storage."
    Returned_to_Sender = 'RETURNED_TO_SENDER'  # "Returned to Sender"

    def __str__(self):
        return self.value


class Address(BaseModel):
    name1: Union[str, None] = Field(default="", description="Company")   # Company
    name2: Union[str, None] = Field(default="", description="Contact Name")   # Contact Name
    name3: Union[str, None] = Field(default="", description="name3")  # c/o
    street1: Union[str, None] = Field(default="", description="Street and number")  # Street and number
    zipCode: Union[str, None] = Field(default="", description="Zip code")
    city: Union[str, None] = Field(default="", description="City")
    province: Union[str, None] = Field(default="", description="Province")
    country: Union[str, None] = Field(default="", description="Country Code")
    email: Union[str, None] = Field(default="", description="Email address of the address")
    telephone: Union[str, None] = Field(default="", description="Telephone number of the address")
    mobile: Union[str, None] = Field(default="", description="Mobile number of the address")
    fax: Union[str, None] = Field(default="", description="Fax number of the address")


class Event(BaseModel):
    timestamp: str = Field(default="", description="Timestamp of the event")
    location: str = Field(default="", description="Location of the event")
    description: str = Field(default="", description="Description of the event")
    country: str = Field(default="")


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
    status: str = Field(default="", description="Status of the parcel")
    events: List[Event] = Field(default=[], description="List of events related to the parcel")
    locationUrl: str = Field(default="", description="Hyperlink of the location of the parcel")

    @classmethod
    def default(cls):
        return cls(weight=1.0, width=0.0, height=0.0, length=0.0,
                   comment="", content="", value=0.0, status="", events=[])


class StandardShipment(BaseModel):
    carrier: str = Field(default="", description="Name of the carrier")
    shipper: Union[Address, None] = Field(default=None, description="Address of the shipper")
    consignee: Union[Address, None] = Field(default=None, description="Address of the consignee")
    parcels: List[Parcel]
    references: List[str]
    location: str = Field(default="", description="Hyperlink of the location of the parcels")
    label: str = Field(default="", description="Label of the shipment in base64 format")
    createdAt: str = Field(default="", description="Timestamp of the creation of the shipment")


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
