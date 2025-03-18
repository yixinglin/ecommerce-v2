import { get_method, apiCrmGeoUrl } from "./common";

export function get_list_geo_contacts({ longitude, latitude, radius, is_calc_distance, include_leads }) {    
    const url = `${apiCrmGeoUrl}/contacts?longitude=${longitude}&latitude=${latitude}&radius=${radius}&is_calc_distance=${is_calc_distance}&include_leads=${include_leads}`;
    return get_method(url);
}

export function fetch_route_on_map({ start_latitude, start_longitude, end_latitude, end_longitude }) {    
    const url = `${apiCrmGeoUrl}/route?lat0=${start_latitude}&lon0=${start_longitude}&lat1=${end_latitude}&lon1=${end_longitude}&mode=driving`;
    return get_method(url);
}



