import json
import os
from typing import List
from pydantic import BaseModel, Field
import utils.stringutils as stringutils
from core.config2 import settings
from models.shipment import StandardShipment

"""
Gls API Key Model
"""
class GlsApiKey(BaseModel):
    url: str
    alias: str
    username: str
    password: str
    shipperId: str

    @classmethod
    def from_json(cls, index):
        """
        Load API key from JSON file
        :param keyName: Name of the API key in the JSON file
        :return:
        """
        file_path = os.path.join('conf', 'apikeys',
                                 settings.api_keys.gls_access_key)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = cls(**data["keys"][index])
        return k

"""
Gls Request Body Model
"""
class Address(BaseModel):
    name1: str
    name2: str
    name3: str
    street1: str
    country: str
    zipCode: str
    city: str
    email: str
    phone: str
    mobile: str

class Addresses(BaseModel):
    delivery: Address

class Service(BaseModel):
    name: str = Field(default="flexdeliveryservice")

    @classmethod
    def flexDeliveryService(cls):
        return cls(name="flexdeliveryservice")


class Parcel(BaseModel):
    weight: float = Field(default=1.0, description="Weight in kg")
    comment: str
    services: List[Service]


class GLSRequestBody(BaseModel):
    shipperId: str
    references: List[str]
    addresses: Addresses
    parcels: List[Parcel]

    def clearServices(self):
        for parcel in self.parcels:
            parcel.services = []

    @classmethod
    def instance(cls, shipment: StandardShipment):
        delivery = Address(
            name1=shipment.consignee.name1,
            name2=shipment.consignee.name2,
            name3=shipment.consignee.name3,
            street1=shipment.consignee.street1,
            zipCode=shipment.consignee.zipCode,
            city=shipment.consignee.city,
            email=shipment.consignee.email,
            phone=shipment.consignee.telephone,
            mobile=shipment.consignee.mobile,
            country=shipment.consignee.country
        )

        addresses = Addresses(delivery=delivery)

        services = []
        if not (stringutils.isEmpty(delivery.phone) and stringutils.isEmpty(delivery.mobile)):
            services.append(Service.flexDeliveryService())

        parcels = []
        for item in shipment.parcels:
            parcels.append(Parcel(
                weight=item.weight,
                comment=item.comment,
                services=services
            ))

        body = cls(
            shipperId="",
            references=shipment.references,
            addresses=addresses,
            parcels=parcels
        )
        return body


# Http Request
GLS_HEADERS_EU = {
    "Host": "api.gls-group.eu",
    "Accept-Language": "en",
    "Accept-Encoding": "gzip,deflate",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Basic auth"
}

def get_example_gls_request_body() -> GLSRequestBody:
    address = Address(
        name1="MustermannGmbH",
        name2="Peter",
        name3="OG",
        street1="Peter 217",
        country="DE",
        zipCode="22154",
        city="Hamburg",
        email="gogo@mustermann.de",
        phone="01234567")

    service = Service(name="flexdeliveryservice")

    parcel = Parcel(
        weight=1.0,
        comment="Note 1@Test",
        services=[service]
    )

    gls_request_body = GLSRequestBody(
        shipperId="2763fytt",
        references=["O22-123456789"],
        addresses=address,
        parcels=[parcel]
    )
    return gls_request_body


if __name__ == '__main__':
    gls_request_body = get_example_gls_request_body()
    aa = gls_request_body.dict()
    print(gls_request_body)
