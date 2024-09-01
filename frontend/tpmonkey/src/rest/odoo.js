import {tm} from '../utils/http.js'
import {calc_basic_auth_token} from './auth.js'

const username = USERNAME;
const password = PASSWORD;
const base_url = BASE_URL;

export function create_order_from_vip(order_data) {
    const token = calc_basic_auth_token(username, password);
    console.log(token);
    const headers = {
        'Authorization': `Basic ${token}`,
        'Content-Type': 'application/json'    
    }    
    const url = `${base_url}/api/v1/odoo/sales/orders`;
    const data = JSON.stringify(order_data);
    return tm.post(url, data, headers)
}

export function fetch_odoo_quants() {
    const token = calc_basic_auth_token(username, password);
    const headers = {
        'Authorization': `Basic ${token}`,
        'Content-Type': 'application/json'      
    }
    const url = `${base_url}/api/v1/odoo/inventory/quants`;
    return tm.get(url, headers)
}