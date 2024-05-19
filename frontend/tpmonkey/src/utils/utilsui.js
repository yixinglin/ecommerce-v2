function appendButton(text, id, selector, clickHandler) {
    $(document).ready(function() {
        // Create a button element
        var button = $('<button/>', {
            text: text, // Button text
            id: id, // Button ID
            click: clickHandler // Click event handler
        });
        
        // Append the button to the div with id 'button-container'
        $(selector).append(button);
    });

}

//Quote: https://stackoverflow.com/a/61511955
// Wait for element to exist
function waitForElm(selector) {
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                observer.disconnect();
                resolve(document.querySelector(selector));
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}

function setValueToInputElm(inputElm, value) {
    inputElm.focus();
    inputElm.setAttribute("value", value)
    let evt = document.createEvent('HTMLEvents');
    evt.initEvent('input', true, true);
    evt.eventType = 'message';
    inputElm.dispatchEvent(evt);
}

// Message show up
function Toast(msg, duration){  
    duration=isNaN(duration)?3000:duration;  
    var m = document.createElement('div');  
    m.innerHTML = msg;  
    m.style.cssText="font-size: .32rem;color: rgb(255, 255, 255);background-color: rgba(0, 0, 0, 0.6);padding: 10px 15px;margin: 0 0 0 -60px;border-radius: 4px;position: fixed;    top: 50%;left: 50%;width: 430px;text-align: center;";
    document.body.appendChild(m);  
    setTimeout(function() {  
        var d = 0.5;
        m.style.opacity = '0';  
        setTimeout(function() { document.body.removeChild(m) }, d * 1000);  
    }, duration);  
}  

function listen_ctrl_key_event(key, callback) {
    $(document).ready(function() {
        //Listening for Ctrl+ [key] using keydown
        $(document).on('keydown', function(event) {
            if ((event.ctrlKey || event.metaKey) && event.key === key) {
                callback(event);
            }
        });
    });
}


function demo() {
    console.log("Hello from utilsui.js!");
    return "";
}

export {appendButton, demo, waitForElm, setValueToInputElm, Toast, listen_ctrl_key_event };





