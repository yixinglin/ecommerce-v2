import tm from '../utils/http.js'

const apiUrl = `${BASE_URL}/api/v1/carriers/gls`;

function bulkCreateGlsLabels(data) {

    return tm.post(`${apiUrl}/shipments/bulk`, data,
        {"Content-Type": "application/json"}, 'json');
}

function getGlsLabelByReference(reference) {
    
}

export { bulkCreateGlsLabels };