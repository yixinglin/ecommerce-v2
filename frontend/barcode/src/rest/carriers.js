import { apiUrl, delete_method, get_method, post_method } from './common';
import { apiCarriersUrl } from './common';

export function create_gls_shipment({payload}) {
    // /api/v1/carriers/gls/shipments
    return post_method(apiCarriersUrl + '/gls/shipments', payload);
}

export function get_gls_shipping_label_url({reference}) {
    //  /api/v1/carriers/gls/shipments/view
    const url = `${apiCarriersUrl}/gls/shipments/view?ref=${reference}`;
    return url;   
}

export function delete_gls_shipment({reference}) {
    return delete_method(apiCarriersUrl + `/gls/shipments/${reference}`);
}


// Large Language Model 
export function parse_address({address}) {
    return post_method(apiUrl + '/llm/parser/address', {address});
}