from typing import Optional, Tuple, List

from fastapi import APIRouter, HTTPException

from core.config2 import settings
from external.common.geometry import fetch_route, GeoPoint, GeoRoute, fetch_table, address_to_coordinates
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

@crm_geo.get("/contacts/keyword/{keyword}", response_model=ListGeoContacts,
             summary="Get customers by keyword")
def get_geo_contact_by_keyword(keyword: str, limit:int=20):
    try:
        with OdooGeoService(key_index=odoo_access_key_index, login=None) as service:
            customers = service.query_contact_by_keyword(keyword.strip(), limit=limit)
    except RuntimeError as e:
        return HTTPException(status_code=500, detail=str(e))
    return ListGeoContacts(
        contacts=customers,
        total=len(customers)
    )

@crm_geo.post("/route",
             response_model=GeoRoute,
             summary="Calculate the route between two locations"
             )
def calc_route(lat0, lon0, lat1, lon1, mode='driving'):
    source = GeoPoint(latitude=lat0, longitude=lon0)
    destination = GeoPoint(latitude=lat1, longitude=lon1)
    return fetch_route(source, destination, mode=mode)

@crm_geo.post("/route/batch",
              response_model=List[GeoRoute],
              summary="Calculate the route between multiple locations (as a list of tuples of (lat, lon))"
              )
def calc_routes(
        locations: List[GeoPoint],
        mode: str = 'driving'):
    # Calculate the route between multiple locations
    routes = []
    for i in range(len(locations) - 1):
        source = locations[i]
        destination = locations[i+1]
        routes.append(fetch_route(source, destination, mode=mode))
    return routes

@crm_geo.post("/address_to_coord",
              response_model=GeoPoint,
              summary="Convert an address to coordinates"
              )
def convert_address_to_coordinates(address: str) -> GeoPoint:
    # Convert an address to coordinates
    coordinates = address_to_coordinates(address)
    if coordinates is None:
        raise HTTPException(status_code=400, detail="Invalid address")
    return coordinates

@crm_geo.post("/route/duration_matrix",
              response_model=dict,
              summary="Calculate the duration matrix between multiple locations (as a list of tuples of (lat, lon))")
def calc_duration_matrix(
        locations: List[GeoPoint],
        mode: str = 'driving',
):
    # Calculate the duration matrix calculation
    return fetch_table(locations, mode=mode)

