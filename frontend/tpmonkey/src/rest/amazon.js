import tm from '../utils/http.js'

const apiUrl = `${BASE_URL}/api/v1/amazon`;

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

export { getUnshippedOrders, getSellerCenterUrls, 
    parsePackSlips, uploadPackSlipsToRedisCache }