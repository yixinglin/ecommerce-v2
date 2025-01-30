import axios from 'axios';

export function calc_token() {
    const username = import.meta.env.VITE_ECM_API_USERNAME;
    const password = import.meta.env.VITE_ECM_API_PASSWORD;    
    const token = btoa(`${username}:${password}`);
    return token;
}

export function get_method(url, args) {      
    var headers_ = {};
    if (args !== undefined && args.headers !== undefined) {        
        headers_ = args.headers;        
    } else {
        headers_['Content-Type'] = 'application/json';
    }   
    headers_['Authorization'] = `Basic ${calc_token()}`;        
    return axios.get(url, { headers: headers_ });
}

export function post_method(url, body, args) { 
    var headers_ = {};
    if (args !== undefined && args.headers !== undefined) {        
        headers_ = args.headers;
    } else {
        headers_['Content-Type'] = 'application/json';        
    }   
    headers_['Authorization'] = `Basic ${calc_token()}`;        
    return axios.post(url, body, { headers: headers_ });
}

export function delete_method(url) {
    const headers = {};
    headers['Authorization'] = `Basic ${calc_token()}`;    
    headers['Content-Type'] = 'application/json';
    return axios.delete(url, { headers: headers });
}

export function put_method(url, body) {
    const headers = {};
    headers['Authorization'] = `Basic ${calc_token()}`;    
    headers['Content-Type'] = 'application/json';
    return axios.put(url, body, { headers: headers });
}

export function put_method_form(url, body) {
    const headers = {};
    headers['Authorization'] = `Basic ${calc_token()}`;    
    headers['Content-Type'] = 'multipart/form-data';
    return axios.put(url, body, { headers: headers });
}