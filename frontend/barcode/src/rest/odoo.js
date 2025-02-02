import { get_method, put_method, put_method_form } from './common';

const domain = import.meta.env.VITE_ECM_API_URL;
const port = import.meta.env.VITE_ECM_API_PORT;

const baseUrl = `http://${domain}:${port}`;
const apiUrl = `http://${domain}:${port}/api/v1`;
const apiScannerUrl = `http://${domain}:${port}/api/v1/scanner`;

export function fetch_all_products_brief(kw) {
    return get_method(apiScannerUrl + '/product/kw/' + kw)
       .then(response => {            
            if (response.status === 200 ) {
                response.data.forEach(product => {
                    product.image_url = `${baseUrl}${product.image_url}`;
                });
            }
            return response;
       })
}

export function fetch_product_by_id(id) {
    return get_method(apiScannerUrl + '/product/pid/' + id)
       .then(response => {
            if (response.status === 200 ) {
                response.data.image_url = `${baseUrl}${response.data.image_url}`;
            }
            return response;
       })
}

export function update_product_weight(id, weight) {
    var weight_float = parseFloat(weight);
    if (isNaN(weight_float)) {
        throw new Error('Invalid weight value');
    }
    return put_method(apiScannerUrl + `/product/pid/${id}/weight/${weight_float}`, {});    
}

export function update_product_barcode(id, barcode) {
    return put_method(apiScannerUrl + `/product/pid/${id}/barcode/${barcode}`, {});    
}

export function update_product_image(id, image) {    
    return put_method_form(apiScannerUrl + '/product/pid/' + id + '/image', image)
        .then(response => {
            if (response.status === 200 ) {
                response.data.image_url = `${baseUrl}${response.data.image_url}`;
            }
            return response;
        })
}

export function fetch_stock_by_product_id(id) {
    return get_method(apiScannerUrl + `/product/pid/${id}/quants`);
}

export function update_inventory_quantity(quant_id, inv_quantity) {    
    return put_method(apiScannerUrl + `/product/qid/${quant_id}/qty/${inv_quantity}`, {});
}

export function quant_relocation_by_id(quant_id, location_barcode) {    
    return put_method(apiScannerUrl + `/product/qid/${quant_id}/relocation/to_location/${location_barcode}`, {});
}

export function fetch_packaging_by_product_id(id) {    
    return get_method(apiScannerUrl + `/product/pid/${id}/packaging`);
}

export function update_packaging_barcode(pack_id, barcode) {    
    return put_method(apiScannerUrl + `/product/pkid/${pack_id}/barcode/${barcode}`, {});
}

export { baseUrl, apiScannerUrl };