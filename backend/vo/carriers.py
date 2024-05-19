
from typing import List
from pydantic import BaseModel, Field


class ShipmentVO(BaseModel):
    references: List[str] = Field(description="The list of references of the shipment")
    carrier_name: str = Field(description="The name of the carrier")
    alias: str = Field(description="The alias of the shipment account")
    trackNumbers: List[str] = Field(description="The list of tracking numbers of the shipment")
    trackingUrls: List[str] = Field(description="The list of tracking urls of the shipment")
    contents: List[str] = Field(description="The content of the parcels in the shipment")
    createdAt: str = Field(description="The date and time when the shipment was created")
    labels: str = Field(description="The base64 encoded pdf of the shipment labels")
    new: bool = Field(description="True if the shipment is new, False otherwise")
    messages: List[str] = Field(description="The list of messages associated with the shipment")

    name1: str = Field(description="The name of the first recipient")
    name2: str = Field(default=None, description="The name of the second recipient")
    name3: str = Field(default=None, description="The name of the third recipient")
    street1: str = Field(description="The street address of the first recipient")
    city: str = Field(description="The city of the first recipient")
    province: str = Field(description="The province of the first recipient")
    zipCode: str = Field(description="The zip code of the first recipient")
    country: str = Field(description="Country ")


    def to_list(self):
        return [self.createdAt,  ";".join(self.references),
                self.country, self.province, self.zipCode, self.city,  self.street1,
                self.name1, self.name2, self.name3,
                ";".join(self.trackNumbers), ";".join(self.contents),
                self.new, ";".join(self.messages), self.carrier_name, self.alias,]


class CreatedShipmentVO(BaseModel):
    """
    The response model for the createShipment endpoint
    """
    id: str = Field(description="The id of the created shipment")
    status: int = Field(description="The status of the created shipment")
    message: str = Field(description="The message associated with the created shipment")

class PickSlipItemVO(BaseModel):
    """
    The response model for the getPickSlip endpoint
    """
    date: str = Field(description="The date of the pick slip")
    carrier: str = Field(description="The name of the carrier")
    orderId: str = Field(description="The id of the b2c order")
    trackId: str = Field(description="The id of the tracking number")
    parcelNumber: str = Field(description="The parcel number of the shipment")
    sku: str = Field(description="The sku of the product")
    title: str = Field(description="The title of the product")
    quantity: int = Field(description="The quantity of the product")
    storageLocation: str = Field(description="The storage location of the product")
    imageUrl: str = Field(description="The image url of the product")
    street1: str = Field(description="The street address of the recipient")

