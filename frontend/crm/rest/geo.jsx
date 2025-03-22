import { get_method, post_method, apiCrmGeoUrl } from "./common";

export function get_list_geo_contacts({ longitude, latitude, radius, is_calc_distance, include_leads }) {
    const url = `${apiCrmGeoUrl}/contacts?longitude=${longitude}&latitude=${latitude}&radius=${radius}&is_calc_distance=${is_calc_distance}&include_leads=${include_leads}`;
    return get_method(url);
}

export function get_geo_contacts_by_keyword(keyword) {
    const url = `${apiCrmGeoUrl}/contacts/keyword/${keyword}?limit=10`;
    return get_method(url);
}

export function fetch_route_on_map({ start_latitude, start_longitude, end_latitude, end_longitude }) {
    const url = `${apiCrmGeoUrl}/route?lat0=${start_latitude}&lon0=${start_longitude}&lat1=${end_latitude}&lon1=${end_longitude}&mode=driving`;
    return post_method(url, {});
}

export function fetch_batch_routes_on_map(list_positions) {
    /**
     *    //   list_positions =  [
          //     {
          //       "latitude": 0,
          //       "longitude": 0,
          //       "name": "string"
          //     }
          //   ]
     */
    const url = `${apiCrmGeoUrl}/route/batch`;
    return post_method(url, list_positions);
}

export function address_to_coordinates(address) {
    const url = `${apiCrmGeoUrl}/address_to_coord?address=${address}`;
    return post_method(url, {});
}

export async function customer_address_to_coordinate(keyword) {    
    const response = await get_geo_contacts_by_keyword(keyword);    
    if (response.data.contacts.length > 0) {
        // Search for customer location from Odoo
        const contact = response.data.contacts[0];
        response.data = {
            "latitude": contact.latitude,
            "longitude": contact.longitude,
            "name": contact.name,
        }
        return response;
    } else {
        // Use general api.
        return address_to_coordinates(address);
    }
}


