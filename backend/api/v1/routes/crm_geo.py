from typing import Optional

from fastapi import APIRouter, HTTPException

from core.config2 import settings
from external.common.geometry import fetch_route, GeoPoint, GeoRoute
from schemas.crm_geo import ListGeoContacts
from services.odoo.OdooGeoService import OdooGeoService

crm_geo = APIRouter()

odoo_access_key_index = settings.api_keys.odoo_access_key_index

@crm_geo.get("/contacts", response_model=ListGeoContacts,
             summary="Get customers within a radius of a given location")
def get_geo_contacts(longitude: float, latitude: float,
                      radius: float = 9999,
                      is_calc_distance: bool = False,
                      include_leads: bool = False
                     ):
    try:
        with OdooGeoService(key_index=odoo_access_key_index, login=None) as service:
            if include_leads:
                customers = service.query_all_geo_contacts(offset=0, limit=None)
            else:
                customers = service.query_all_geo_customers(offset=0, limit=None)
            if is_calc_distance:
                customers = service.calc_distance(
                    longitude,
                    latitude,
                    customers,
                )
                customers = [c for c in customers if c.km_distance <= radius]
    except RuntimeError as e:
        return HTTPException(status_code=500, detail=str(e))
    return ListGeoContacts(
        contacts=customers,
        total=len(customers)
    )

@crm_geo.get("/route",
             response_model=GeoRoute,
             summary="Calculate the route between two locations"
             )
def calc_route(lat0, lon0, lat1, lon1, mode='driving'):
    source = GeoPoint(latitude=lat0, longitude=lon0)
    destination = GeoPoint(latitude=lat1, longitude=lon1)
    return fetch_route(source, destination, mode=mode)


def calc_duration_matrix():
    # TODO: Implement duration matrix calculation
    pass