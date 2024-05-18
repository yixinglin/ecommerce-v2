import { appendButton, demo } from '../utils/utilsui.js';
import { getUnshippedOrders, getSellerCenterUrls, parsePackSlips } from '../rest/amazon.js';
import { bulkCreateGlsLabels } from '../rest/gls.js';
import tm from '../utils/http.js'

//过滤器 -ERR_FAILED -KatalMetricsSellerCentral -Vibes -chrome-extension

const apiUrl = `${BASE_URL}/api/v1/resource`;
console.log(`apiUrl: ${apiUrl}`);

class AmazonOrderList {
    // App applied to the Amazon Order List page
    constructor() {
        console.log(`AmazonOrderList host`);
        // Order numbers of the unshipped orders
        this.unshippedOrders = [];
        // Request body for bulk create parcel labels
        this.packSlips = [];
        // Order numbers with parcel labels created. They will be confirmed shipment later.
        this.toShippedOrders = [];
        this.mountPoint = ".myo-bulk-action-panel-left";
    }

    toLoad() {
        // Validate if the page is the Amazon Order List page
        // Check if element exists
        if (!document.querySelector('.total-orders-heading')) {
            return false;
        } else {
            return true;
        }
    }

    mount() {
        // Append the first button to get unshipped orders
        if (!this.toLoad()) {
            console.log('Not Amazon Order List page');
            return;
        }
        this.appendButton1();
    }

    appendButton1() {
        // Append the first button to get unshipped orders
        appendButton('[1] 未发货订单', 'check-unshipped', this.mountPoint,
            (event) => { this.button1Handler(event) })
    }

    appendButton2() {
        // Append the second button to upload shipping slips
        appendButton('[2] 上传送货单', 'upload-shipping-slips', this.mountPoint,
            (event) => this.button2Handler(event))

    }

    appendButton3() {
        // Append the third button to create GLS labels
        appendButton('[3] 生成快递单(GLS)', 'create-gls-labels', this.mountPoint,
            (event) => { this.button3Handler(event)})
    }
    appendButton4() {
        // Append the fourth button to download csv report
        appendButton('[4] 下载CSV报告', 'download-csv-report', this.mountPoint,
            (event) => {this.button4Handler(event);})
    }

    appendButton5() {
        // Append the fifth button to bulk confirm orders
        appendButton('[5] 批量确认', 'bulk-confirm-orders', this.mountPoint,
            (event) => {this.button5Handler(event);})
    }

    /* Button handlers */

    button1Handler(event) {
        // Button handler for the first button
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

    button2Handler(event) {
        // Button handler for the second button
        const button = event.target;
        button.disabled = true;
        console.log(this.unshippedOrders)
        getSellerCenterUrls().then((response) => {
            const { code, data, message } = response;
            this.bulkConfirmUrl = data['bulk-confirm-shipment'];
            this.packSlipUrl = data['packing-slip'];       
        }).then(() => {
            // 1. Download shipping slips for the unshipped orders
            const orderNumbers = this.unshippedOrders.join(';');
            var url = `${this.packSlipUrl}?orderIds=${orderNumbers}`;
            console.log(url);
            url = "https://www.hamster25.buzz/amazon/amazon-delivery-de-03.html";
            console.warn("MOCK");
            return tm.get(url, {}, "text");
        }).then((response) => {
            // 2. Upload shipping slips to the server for processing
            const data = {
                    "country": "DE",
                    "formatIn": "html",
                    "formatOut": "",
                    "data": response,
            }        
            return parsePackSlips(JSON.stringify(data));
        }).then((response) => {
            // 2. Upload shipping slips to the server for processing
            const { code, data, message } = response;
            if (code != 200) {
                throw new Error(message);   
            }
            if (data.length == 0) {
                throw new Error("No shipping slips found");   
            }
            this.packSlips = data;
            alert(`成功解析共${data.length}张送货单`);
            this.appendButton3();
        }).catch(error => {
            console.error(error)
            alert(`送货单解析失败，请重试。错误信息: ${error.message}`);
            button.disabled = false;
        })
    }

    button3Handler(event) {
        const button = event.target;
        button.disabled = true;
        // Button handler for the third button
        alert(`正在生成快递单[${this.packSlips.length}]，请耐心等待几分钟`);
        const ps = JSON.stringify(this.packSlips);
        console.log(ps);
        bulkCreateGlsLabels(ps).then((response) => {
            const { code, data, message } = response;
            console.log(data)
            if (code != 200) {
                throw new Error(message);
            }
            alert(`共生成[${data.length}]张快递单`);     
            this.toShippedOrders = data.map(item => item.id)
            this.appendButton4();
        }).catch(error => {
            console.error(error)
            alert(`快递单生成失败，请重试。错误信息：${error.message}`);
            button.disabled = false;            
        })        
    }

    button4Handler(event) {
        // Button handler for the fourth button
        alert('功能暂未实现');
        const button = event.target;
        button.disabled = true;
        this.appendButton5();
    }

    button5Handler(event) {
        // Button handler for the fifth button
        const button = event.target;
        button.disabled = true;
        // Get the bulk confirm url
        const orderNumbers = this.toShippedOrders.join(';');
        const url = `${this.bulkConfirmUrl}?orderIds=${orderNumbers}`;
        window.open(url);
    }
}

export default AmazonOrderList;