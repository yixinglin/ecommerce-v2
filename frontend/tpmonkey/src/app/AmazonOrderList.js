import { appendButton, demo } from '../utils/utilsui.js';
import { getUnshippedOrders, getSellerCenterUrls, uploadPackSlipsToRedisCache } from '../rest/amazon.js';
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

    // toLoad() {
    //     // Validate if the page is the Amazon Order List page
    //     // Check if element exists
    //     if (!document.querySelector('.total-orders-heading')) {
    //         return false;
    //     } else {
    //         return true;
    //     }
    // }

    mount() {
        waitForElm(this.mountPoint).then(() => {
            this.appendButton1();
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

    appendButton1() {
        // Append the first button to get unshipped orders
        appendButton('[1] 上传未发货订单', 'check-unshipped', this.mountPoint,
            (event) => { this.button1Handler(event) })
    }

    appendButton2() {
        // Append the second button to upload shipping slips
        appendButton('[2] 上传装箱单', 'upload-shipping-slips', this.mountPoint,
            (event) => this.button2Handler(event))
    }

    button1Handler(event) {
        // Get unshipped orders
        const button = event.target;
        button.disabled = true;
        // 1. Get order numbers of the unshipped orders
        getUnshippedOrders().then((response) => {
            const { code, data, message } = response;
            if (code != 200) {
                throw new Error(message);
            }
            this.unshippedOrders = data;
            alert(`成功获取未发货订单 [${data.length}]`);          
            this.appendButton2();  
        }).catch(error => {
            console.error(error)
            alert(`获取未发货订单失败，请重试。 错误信息: ${error.message}`);
            button.disabled = false;
        })
    }

    async button2Handler(event) {
        const button = event.target;
        button.disabled = true;
        console.log(this.unshippedOrders)
        var response = await getSellerCenterUrls();
        var { code, data, message } = response;
        this.bulkConfirmUrl = data['bulk-confirm-shipment'];
        this.packSlipUrl = data['packing-slip'];       
        console.log(this.packSlipUrl);          
        
        // 1. Download shipping slips for the unshipped orders
        const orderNumbers = this.unshippedOrders.orderNumbers.join(';');
        var url = `${this.packSlipUrl}?orderIds=${orderNumbers}`;
        console.log(url);
        url = "https://www.hamster25.buzz/amazon/amazon-delivery-de-03.html";
        console.warn("MOCK");
        response = await tm.get(url, {}, "text");        
        // 2. Upload shipping slips to the server for processing
        response = await uploadPackSlipsToRedisCache(response);
        console.log(response);
        var {code, data, message} = response;
        if (code != 200) {
            throw new Error(message);
        }
        alert(`BatchId: ${data.key}`)
        console.log(data.key)
    }
}

export default AmazonOrderList;