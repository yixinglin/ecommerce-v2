
function makePostRequest(url, payload, headers, responseType = 'json') {
  return new Promise((resolve, reject) => {
    console.log('Making POST request to', url);
    GM_xmlhttpRequest({
      method: "POST",
      url: url,
      data: payload,
      responseType: responseType,
      headers: headers,
      onload: function (response) {
        resolve(response.response);
      },
      onerror: function (error) {
        reject(new Error(`Network error: ${error.error}`));
      }
    });
  });
}

function makeGetRequest(url, headers, responseType = 'json') {
  return new Promise((resolve, reject) => {
    GM_xmlhttpRequest({
      method: "GET",
      url: url,
      responseType: responseType,
      headers: headers,
      onload: function (response) {
        resolve(response.response);
      },
      onerror: function (error) {
        reject(new Error(`Network error: ${error.error}`));
      }
    });
  });
}

// Define the tm object with get and post methods
const tm = {
  get: function (url, headers, responseType) {
    return makeGetRequest(url, headers, responseType);
  },
  post: function (url, payload, headers, responseType) {
    return makePostRequest(url, payload, headers, responseType);
  }
};

export default tm;