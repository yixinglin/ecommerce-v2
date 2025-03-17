from typing import List, Optional
import requests
from pydantic import BaseModel


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

# OSRM API
osrm_api_url = "https://router.project-osrm.org/route"

def fetch_route(source: GeoPoint, destination: GeoPoint, mode: str = "driving") -> GeoRoute:
    url = (f"{osrm_api_url}/v1/{mode}/{source.longitude},{source.latitude};{destination.longitude},{destination.latitude}?"
          f"overview=full&geometries=geojson")
    response = requests.get(url)
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
