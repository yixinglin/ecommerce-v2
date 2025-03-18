import json
import os
from typing import List, Optional
import requests
from pydantic import BaseModel
from core.config2 import settings

class GeoPoint(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None

class GeoRoute(BaseModel):
    source: GeoPoint
    destination: GeoPoint
    duration: float
    distance: float
    coordinates: List[GeoPoint]

class OSRMConfig:

    def __init__(self):
        self.rm_conf_path = settings.api_keys.route_machine
        self.rm_model = settings.api_keys.route_machine_model
        self.rm_provider = settings.api_keys.route_machine_provider

        with open(os.path.join("conf", "apikeys", self.rm_conf_path), "r") as f:
            self.conf = json.load(f)
        self.url = self.conf["osrm"][self.rm_provider]['host']
        self.basic_auth = self.conf["osrm"][self.rm_provider]['basic_auth']

osrm_config = OSRMConfig()

osrm_headers = {
    "Authorization": f"Basic {osrm_config.basic_auth}"
}

def fetch_route(source: GeoPoint, destination: GeoPoint, mode: str = "driving") -> GeoRoute:
    url = (f"{osrm_config.url}/route/v1/{mode}/{source.longitude},{source.latitude};{destination.longitude},{destination.latitude}?"
          f"overview=full&geometries=geojson")
    response = requests.get(url, headers=osrm_headers)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch route from OSRM API: {response.text}")
    data = response.json()
    route = data["routes"][0]
    leg = route['legs'][0]
    s = data["waypoints"][0]
    d = data["waypoints"][-1]
    return GeoRoute(
                    source=GeoPoint(latitude=s["location"][1], longitude=s["location"][0], name=s["name"]),
                    destination=GeoPoint(latitude=d["location"][1], longitude=d["location"][0], name=d["name"]),
                    coordinates=[GeoPoint(latitude=coord[1], longitude=coord[0]) for coord in route["geometry"]["coordinates"]],
                    duration=leg["duration"],
                    distance=leg["distance"]
    )
