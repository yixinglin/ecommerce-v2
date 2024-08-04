import { appendButton, demo } from '../utils/utilsui.js';
// import { getUnshippedOrders, getSellerCenterUrls, uploadPackSlipsToRedisCache } from '../rest/amazon.js';
import { waitForElm } from '../utils/utilsui.js';
import tm from '../utils/http.js'

const apiUrl = `${BASE_URL}`;
console.log(`apiUrl: ${apiUrl}`);

class AmazonOrderList {
    // App applied to the Amazon Order List page
    constructor() {
        console.log(`AmazonOrderList host`);
        // Order numbers of the unshipped orders
        this.unshippedOrders = [];
        this.mountPoint = ".myo-bulk-action-panel-left";
    }


    mount() {
        waitForElm(this.mountPoint).then(() => {
            // this.appendButton1();
            this.addOptionToResultsPerPage();
        })        
    }

    addOptionToResultsPerPage() {
        // Add option to results per page
        const select = document.querySelector('#myo-table-results-per-page');
        const option200 = document.createElement('option');
        option200.value = '200';
        option200.text = '200';
        select.add(option200);
        var option300 = document.createElement('option');
        option300.value = '300';
        option300.text = '300';
        select.add(option300);
    }
}

export default AmazonOrderList;