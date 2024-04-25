from typing import List, Optional
from pydantic import BaseModel

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

class Service(BaseModel):
    name: str

class Parcel(BaseModel):
    weight: float
    comment: str
    services: List[Service]

class GLSRequestBody(BaseModel):
    shipperId: str
    references: List[str]
    addresses: Address
    parcels: List[Parcel]

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
    print(gls_request_body)