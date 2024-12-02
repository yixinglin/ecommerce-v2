
from typing import List, Union
from pydantic import BaseModel, Field


class ShipmentVO(BaseModel):
    references: List[str] = Field(description="The list of references of the shipment")
    carrier_name: str = Field(description="The name of the carrier")
    alias: str = Field(description="The alias of the shipment account")
    trackNumbers: List[str] = Field(description="The list of tracking numbers of the shipment")
    parcelNumbers: List[str] = Field(description="The list of parcel numbers of the shipment")
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
    date: Union[str, None] = Field(default=None, description="The date of the pick slip")
    carrier: Union[str, None] = Field(default=None, description="The name of the carrier")
    orderId: Union[str, None] = Field(default=None, description="The id of the b2c order")
    trackId: Union[str, None] = Field(default=None, description="The id of the tracking number")
    parcelNumber: Union[str, None] = Field(default=None, description="The parcel number of the shipment")
    sku: Union[str, None] = Field(default=None, description="The sku of the product")
    title: Union[str, None] = Field(default=None, description="The title of the product")
    quantity: Union[int, None] = Field(default=None, description="The quantity of the product")
    storageLocation: Union[str, None] = Field(default=None, description="The storage location of the product")
    imageUrl: Union[str, None] = Field(default=None, description="The image url of the product")
    street1: Union[str, None] = Field(default=None, description="The street address of the recipient")
    city: Union[str, None] = Field(default=None, description="The city of the recipient")
    country: Union[str, None] = Field(default=None, description="Country of the recipient")
    productBarcode: Union[str, None] = Field(default=None, description="The barcode of the product")
    orderKey: Union[str, None] = Field(default=None, description="The key of the order. To identify whether orders contains the same products and quantities")
    taskId: Union[int, None] = Field(default=None, description="The id of the task")
    purchasedAt: Union[str, None] = Field(default=None, description="The date of the purchase")
    zipCode: Union[str, None] = Field(default=None, description="The zip code of the recipient")
    city: Union[str, None] = Field(default=None, description="The city of the recipient")
    note: Union[str, None] = Field(default=None, description="The note of the pick slip item")


