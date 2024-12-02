import {tm} from '../utils/http.js';
import { makePostRequest, convertJsonToForm } from '../utils/http.js';
import {Toast} from '../utils/utilsui.js';
import {calc_basic_auth_token} from './auth.js'

const apiUrl = `${BASE_URL}/api/v1/carriers/gls`;
const headers = {
    'Authorization': `Basic ${calc_basic_auth_token(USERNAME, PASSWORD)}`,    
}  

function bulkCreateGlsLabels(data) {

    return tm.post(`${apiUrl}/shipments/bulk`, data,
        headers);
}

function getGlsShipmentsByReference(reference) {
    // 'http://127.0.0.1:5018/api/v1/carriers/gls/shipments?refs=O12308132sdddd332ss&labels=true'
    return tm.get(`${apiUrl}/shipments?refs=${reference}&labels=false`, headers);    
}

function getGlsShipmentsViewByReference(reference) {
    //'http://127.0.0.1:5018/api/v1/carriers/gls/shipments/view?ref=O123081227434A432sddd332ss'
    return tm.get(`${apiUrl}/shipments/view?ref=${reference}`, headers);
}

function createGlsLabel(data) {
    console.log("createGlsLabel: ", data);        
    const payload = JSON.stringify(data);
    let headers_ = {"Content-Type": "application/json", ...headers};
    return tm.post(`${apiUrl}/shipments`, payload, headers_)
}

function displayGlsLabel(htmlContent) {
    let glswin = window.open ("", "GLS Label", "location=no,status=no,scrollvars=no,width=800,height=900");
    glswin.document.write(htmlContent);
}

// TODO: 下面是最原始的GLS接口，后续会弃用
var Carriers = {
    createGlsLabel: function(url, data, callback) {
        console.log("createGlsLabel", data);
        var headers = {"Content-Type": "application/x-www-form-urlencoded"};
        makePostRequest(url, convertJsonToForm(data), headers).then(resp => {
            let glswin = window.open ("", "GLS Label", "location=no,status=no,scrollvars=no,width=800,height=900");
            glswin.document.write(resp.responseText);
            if (callback) {
                var trackId = glswin.document.getElementById("trackId-1").textContent;
                callback(trackId.replace("|", "").trim())
            }
        }).catch(resp => {
            console.log(resp.responseText);
            Toast("Error", 1000)
        });
    }
}


export { bulkCreateGlsLabels, createGlsLabel, getGlsShipmentsByReference, getGlsShipmentsViewByReference, displayGlsLabel, Carriers };