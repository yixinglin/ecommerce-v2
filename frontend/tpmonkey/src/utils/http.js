
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

function makeGetRequest(url, headers) {
  return new Promise((resolve, reject) => {
    GM_xmlhttpRequest({
      method: "GET",
      url: url,
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


function getCookieByName(name) {
  // Construct the name of the cookie followed by an equals sign
  const nameEQ = name + "=";

  // Split the document.cookie string into individual cookies
  const cookies = document.cookie.split(';');

  // Loop through each cookie
  for(let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();

      // If the cookie starts with the name we're looking for, return its value
      if (cookie.indexOf(nameEQ) === 0) {
          return cookie.substring(nameEQ.length, cookie.length);
      }
  }

  // If the cookie is not found, return null
  return null;
}



// Define the tm object with get and post methods
const tm = {
  get: function (url, headers) {
    return makeGetRequest(url, headers);
  },
  post: function (url, payload, headers) {
    return makePostRequest(url, payload, headers);
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
  makeGetRequest, makePostRequest, convertJsonToForm, tm, getCookieByName,
};