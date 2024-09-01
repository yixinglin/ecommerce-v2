import { waitForElm} from '../utils/utilsui.js';
import {getCookieByName, tm} from '../utils/http.js';
import {create_order_from_vip} from '../rest/odoo.js'
class VipOrderDetails {

    constructor(baseurl) {
        console.log("VipOrderDetails constructor called");        
        console.log("Base URL: ", baseurl);
        this.vipDomain = "http://vip.hansagt-med.com";
        this.baseurl = baseurl;        
    }

    init() {
        const token = getCookieByName('Admin-Token');
        this.headers = {
            'Authorization': `Bearer ${token}`,            
            'Accept': 'application/json, text/plain, */*'
        };  
        this.orderId = window.location.href.split('/').pop();
    }

    mount() {
        console.log("VipOrderDetails mounted");
        waitForElm('.el-descriptions').then(() => {
            console.log("vip-order-details found");
            this.init();
            this.#addButtonTo('.app-container', 
                'create-odoo-order-btn', 
                'Upload to Odoo', () => {this.handleUploadToOdoo()});
            });
    }

    async handleUploadToOdoo() {
        console.log("handleUploadToOdoo called");
        var resp = await this.#fetchOrderLinesFromVipServer();
        const orderLines = JSON.parse(resp.response);
        resp = await this.#fetchOrderFromVipServer();
        const order = JSON.parse(resp.response).data;
        const odoo_order = this.#toOdooOrder(order, orderLines);
        console.log("Odoo Order Formatted: ", odoo_order);
        create_order_from_vip(odoo_order).then(res => {
            const state_code = res.status;
            const data = JSON.parse(res.responseText).data;
            
            if (state_code === 200) {
                alert(`Odoo Order created for 【${data.contact_name}】`);
                console.log("Odoo Order created successfully", data);
            } else {
                console.log(`Error creating Odoo Order. ${res.response}`);
                alert(`Error creating Odoo Order. ${res.response}`);
            }            
            
        }).catch(err => {
            alert("Error creating Odoo Order");
            console.error("Error creating Odoo Order", err);
        });
    }

    #fetchOrderLinesFromVipServer() {
        const reqUrl = this.vipDomain + 
            '/prod-vip-api/vip/order/item/list?orderId=' + 
            this.orderId + '&pageSize=1000';        
        return tm.get(reqUrl, this.headers);
    }

    #fetchOrderFromVipServer() {        
        const reqUrl = this.vipDomain + 
            '/prod-vip-api/vip/order/order/' + this.orderId;
        return tm.get(reqUrl, this.headers);
    }

    #toOdooOrder(order, orderLines) {        
        const rows = orderLines.rows;
        var orderLines_ = [];
        for(let i=0; i<rows.length; i++) {
            const r = rows[i];
            const line_ = {
                productName: r.productName,
                sellerSKU: r.articleNumber,
                quantity: r.quantity,
                price: r.price,                
                unit: r.unit,
            }
            orderLines_.push(line_);
        }

        var shipAddress_ = {};
        shipAddress_.name1 = order.customerName;
        shipAddress_.name2 = order.contact;
        shipAddress_.email = order.email;
        shipAddress_.telephone = order.phone;
        shipAddress_.street1 = order.address;  

        var order_ = {};
        order_.orderId = order.orderCode;
        order_.orderLines = orderLines_;        
        order_.shipAddress = shipAddress_;
        return order_;
    }

    #extractDataFromOrder() {
        console.log("extractDataFromOrder called");
        const order = {};
        const orderLines = [];
        const orderLineElements = document.querySelectorAll('.el-table__body-wrapper tbody tr');        
        // #app > div.app-wrapper.hideSidebar.withoutAnimation > div.main-container.hasTagsView > section > div > div:nth-child(2) > div > table > tbody:nth-child(1) > tr > td:nth-child(1) > div > span.el-descriptions-item__content
        for(let i=0; i<orderLineElements.length; i++) {
            const rowEl = orderLineElements[i];
            const articleNumber = rowEl.querySelector("td:nth-child(2)").textContent;
            var quantity = rowEl.querySelector("td:nth-child(3)").textContent;            
            quantity = parseInt(quantity);
            var price = rowEl.querySelector("td:nth-child(4)").textContent;            
            price = parseFloat(price);
            const productName = rowEl.querySelector("td:nth-child(1)").textContent;
            orderLines.push({
                articleNumber, 
                quantity, 
                price, 
                productName
            });            
        }
        order.orderLines = orderLines;
        return order;
    }

    #addButtonTo(selector, id, name, callback) {
        const container = document.querySelector(selector);
        const button = document.createElement("button");
        button.innerText = name;
        button.id = id;
        button.addEventListener("click", callback);
        container.appendChild(button);        
    }



}

export default VipOrderDetails;

/*
Create Odoo Order Request Body:
{
    "orderId": "string",
    "orderLines": [
      {
        "quantity": 0,
        "sellerSKU": "string",
        "unit": "string",
        "productName": "string",
        "price": 0
      }
    ],
    "shipAddress": {
      "name1": "",
      "name2": "",
      "name3": "",
      "street1": "",
      "zipCode": "",
      "city": "",
      "province": "",
      "country": "",
      "email": "",
      "telephone": "",
      "mobile": "",
      "fax": ""
    }
  }
*/
