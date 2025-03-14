import { get_method, apiCrmGeoUrl } from "./common";

export function get_list_geo_contacts({ longitude, latitude, radius, is_calc_distance, include_leads }) {    
    const url = `${apiCrmGeoUrl}/contacts?longitude=${longitude}&latitude=${latitude}&radius=${radius}&is_calc_distance=${is_calc_distance}&include_leads=${include_leads}`;
    return get_method(url);
}



