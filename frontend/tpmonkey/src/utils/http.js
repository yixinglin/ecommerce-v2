
function makePostRequest(url, payload, headers) {
  return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
      method: "POST",
      url: url,
      data: payload,
      headers: headers,
      onload: function(response) {
          resolve(response);
      },
      onerror: function(error) {
          reject(error);
      }
      });
  });
}

function makeGetRequest(url) {
  return new Promise((resolve, reject) => {
    GM_xmlhttpRequest({
      method: "GET",
      url: url,
      onload: function(response) {
        resolve(response);
      },
      onerror: function(error) {
        reject(error);
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

// Json to form
function convertJsonToForm(data) {
  var ans = Object.keys(data).map(function(k) {
      return encodeURIComponent(k) + '=' + encodeURIComponent(data[k])
  }).join('&')
  return ans
}

export {
  makeGetRequest, makePostRequest, convertJsonToForm, tm, 
};