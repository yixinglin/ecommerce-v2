from typing import Optional

from pydantic import BaseModel


class GeoContact(BaseModel):
    id: int
    name: str
    branch: str
    email: str
    phone: str
    mobile: str
    street: str
    street2: str
    zip: str
    city: str
    customer_rank: int
    is_customer: bool
    country_code: str
    total_invoiced: float
    active: bool
    longitude: float
    latitude: float
    km_distance: float = 9999
    sales_person_id: int
    sales_person: Optional[str] = None

class ListGeoContacts(BaseModel):
    contacts: list[GeoContact]
    total: int
