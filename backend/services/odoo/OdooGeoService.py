from typing import Optional, List

from pydantic import BaseModel

from core.log import logger
from schemas.crm_geo import GeoContact
from services.odoo import OdooContactService
import pandas as pd
from utils.utils_math import haversine_vectorized


class OdooGeoService:

    def __init__(self, key_index, login=True, *args, **kwargs):
        self.key_index = key_index
        self.svc_contact = OdooContactService(key_index, login=login)
        self.mdb_contact = self.svc_contact.mdb_contact
        self.api = self.svc_contact.api
        self.login = login

    def __enter__(self):
        self.svc_contact.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.svc_contact.__exit__(exc_type, exc_val, exc_tb)

    def to_geo_contact(self, contact: dict) -> GeoContact:
        get_str_value = lambda k: "" if contact[k] == False else contact[k]
        geo_contact = GeoContact(
            id=contact['id'],
            name=contact['complete_name'],
            branch= "" if contact['industry_id'] == False else contact['industry_id'][1],
            email=get_str_value("email"),
            phone=get_str_value("phone"),
            mobile=get_str_value("mobile"),
            street=get_str_value("street"),
            street2=get_str_value("street2"),
            zip=get_str_value("zip"),
            city=get_str_value("city"),
            country_code=get_str_value('country_code'),
            customer_rank=contact['customer_rank'],
            is_customer=contact['customer_rank'] > 0,
            total_invoiced=contact['total_invoiced'],
            active=contact['active'],
            longitude=contact['partner_longitude'],
            latitude=contact['partner_latitude'],
            sales_person_id=-1 if contact['user_id'] == False else contact['user_id'][0],
            sales_person="" if contact['user_id'] == False else contact['user_id'][1],
        )
        return geo_contact

    def calc_distance(self, lon0, lat0,
                      geo_contacts: List[GeoContact]) -> List[GeoContact]:
        # Calculate distance between geo_contacts and lon0, lat0
        df_geo_contacts = pd.DataFrame.from_dict([c.dict() for c in geo_contacts])
        df_geo_contacts['km_distance'] = haversine_vectorized(
            lat0,
            lon0,
            df_geo_contacts['latitude'],
            df_geo_contacts['longitude'],
        )
        df_geo_contacts.sort_values(by='km_distance', inplace=True)
        list_geo = []
        for contact in df_geo_contacts.to_dict('records'):
            gc = GeoContact(**contact)
            list_geo.append(gc)
        return list_geo


    def query_all_geo_contacts(self, offset, limit, min_customer_rank=0) -> List[GeoContact]:
        filter_ = {
            "alias": self.api.get_alias(),
            "data.customer_rank": {"$gte": min_customer_rank},
            "data.is_company": True,
            "data.active": True,
        }
        data = self.mdb_contact.query_contacts(offset=offset, limit=limit, filter=filter_)
        list_geo = []
        for contact in data:
            try:
                geo_contact = self.to_geo_contact(contact['data'])
                list_geo.append(geo_contact)
            except KeyError as e:
                logger.error(f"Error parsing contact id={contact['data']['id']}: {e}")
        return list_geo

    def query_all_geo_customers(self, offset, limit) -> List[GeoContact]:
        return self.query_all_geo_contacts(offset, limit, min_customer_rank=1)
