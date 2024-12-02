import {tm} from '../utils/http.js';
import {calc_basic_auth_token} from './auth.js'

const apiUrl = `${BASE_URL}/api/v1/amazon`;

const headers = {
    'Authorization': `Basic ${calc_basic_auth_token(USERNAME, PASSWORD)}`,    
}  


function getUnshippedOrders() {
    return tm.get(`${apiUrl}/orders/unshipped?up_to_date=true`, {}, 'json');
}

function getSellerCenterUrls() {    
    return tm.get(`${apiUrl}/orders/sc-urls`, {}, 'json');
}

function parsePackSlips(data) {
    return tm.post(`${apiUrl}/orders/packslip/parse`, data, 
        {"Content-Type": "application/json"}, 'json');
}

function uploadPackSlipsToRedisCache(data) {
    return tm.post(`${apiUrl}/orders/packslip/cache`, data, 
        {"Content-Type": "text/html"}, 'json');
}

function getCatalogAttributes(asins) {
    // asins is an array of ASINs
    // 'http://127.0.0.1:5018/api/v1/amazon/orders/catalog-attributes?api_key_index=0&country=DE&asins=asaddd&asins=asdsddd'
    // Join ASINs array into a query parameter string
    const asinsParam = asins.map(asin => `asins=${encodeURIComponent(asin)}`).join('&');
    const url = `${apiUrl}/orders/catalog-attributes?country=DE&${asinsParam}`;
    console.log(url);
    return tm.get(url, headers);
}

export { getUnshippedOrders, getSellerCenterUrls, 
    parsePackSlips, uploadPackSlipsToRedisCache, getCatalogAttributes }