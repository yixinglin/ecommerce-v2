import {tm} from '../utils/http.js';
import { makePostRequest, convertJsonToForm } from '../utils/http.js';
import {Toast} from '../utils/utilsui.js';

const apiUrl = `${BASE_URL}/api/v1/carriers/gls`;

function bulkCreateGlsLabels(data) {

    return tm.post(`${apiUrl}/shipments/bulk`, data,
        {"Content-Type": "application/json"}, 'json');
}

function getGlsLabelByReference(reference) {
    
}


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


export { bulkCreateGlsLabels, Carriers };