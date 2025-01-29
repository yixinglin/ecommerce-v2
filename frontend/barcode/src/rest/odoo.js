import { get_method } from './common';

// const domain = import.meta.env.VITE_ECM_API_URL;
// const port = import.meta.env.VITE_ECM_API_PORT;

const domain = 'localhost';
const port = '5018';

const apiUrl = `http://${domain}:${port}/api/v1`;
const apiScannerUrl = `http://${domain}:${port}/api/v1/scanner`;

export function fetch_all_products_brief(kw) {
    return get_method(apiScannerUrl + '/product/kw/' + kw);
}
