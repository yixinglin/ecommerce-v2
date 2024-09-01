import { GermanAddrChecker } from '../../utils/address.js';
import { makeGetRequest, makePostRequest, tm } from '../../utils/http.js';
// Script for temporary monkey

var AmazonApi = {
    /**
     * Get customer information from Amazon API
     * @returns An Promise Object
     */
    fetchShipmentFromApi: function(orderNumber) {
        var blobUrl = `https://sellercentral.amazon.de/orders-api/order/${orderNumber}`;
        return tm.get(blobUrl).then( res => {
            var data = JSON.parse(res.responseText);
            var proxyEmail = data.order.buyerProxyEmail;
            console.log(proxyEmail);
            var blob = data.order.blob;
            var payload = {"blobs": [blob]};
            var headers = {"Acccept": "application/json", "Content-Type": "application/json"}
            return tm.post("https://sellercentral.amazon.de/orders-st/resolve", 
                        JSON.stringify(payload), headers);
        })
    }
}


class GermanLike {

    constructor(dom) {
        this.dom = dom;
        this.countryBlackListMap = {"Schweiz": "ch", "Switzerland": "ch", 
            "United Kingdom": "gb", "Vereinigtes Königreich": "gb",
            "Turkey": "tr", "Türkei": "tr"};
        this.countryWhiteListMap = {"Germany": "de", "Deutschland": "de"};
        this.checkerMap = {
            "Germany": new GermanAddrChecker(), "Deutschland": new GermanAddrChecker(),
        }
    }

    getOrderNumber() {
        this.orderNumber = this.dom.querySelector('span[data-test-id="order-id-value"]').textContent;
        return this.orderNumber;
    }

    needTransparentCode() {
        var transparency = this.dom.querySelector("i.a-transparency-badge");
        if (transparency != null) {
            return true
        } 
        return false;
    }

    getOrderLines() {
        if (this.needTransparentCode()) {
            alert("Need transparent code.");
        }
        const rows = this.dom.querySelectorAll("div.a-spacing-large table.a-keyvalue tr");
        var lines = [];
        for(let i=1; i<rows.length; i++) {
            const tds = rows[i].querySelectorAll("td");
            const status = tds[0].textContent;
            const pn = tds[2].querySelectorAll("div.product-name-column-word-wrap-break-all");
            const productName = tds[2].querySelector("div.more-info-column-word-wrap-break-word").textContent;
            const sku = pn[1].textContent.replace("SKU:", "").trim();
            const asin = pn[0].textContent.replace("ASIN:", "").trim();
            var quantity = tds[4].textContent.trim();
            quantity = parseInt(quantity);
            var price = tds[6].querySelector("span").textContent;
            lines.push({sku, quantity, asin, price, productName, status});
        }
        return lines;
    }

    isDhlParcel(shipment) {
        // Check DHL parcel
        var regPostNumber = /\d{9}/;  // Post number of DHL
        for(let n of [shipment.name1, shipment.name2, shipment.name3, shipment.street]) {
            if (regPostNumber.test(n)) {
                return true;
            }
            const prefix = n.toLowerCase().substring(0, 4);
            if (prefix== 'dhl ' || prefix == 'dhl-' || prefix == 'dhl_' ) {
                return true;
            }
        }
        const street = shipment.street.toLowerCase();
        if (street.includes("packstation") || street.includes("postfiliale")) {
            return true;
        }
        return false;
    }

    isInCountryWhiteList(countryCode) {
        const codeList = Object.values(this.countryWhiteListMap);
        return codeList.includes(countryCode.toLowerCase());
    }

    isInCountryBlackList(countryCode) {
        const codeList = Object.values(this.countryBlackListMap);
        return codeList.includes(countryCode.toLowerCase());
    }

    // Get shipping address from the surface of the website
    parseFromWebSurface() {
        const ivBtn = document.querySelector('span[data-test-id="manage-idu-invoice-button"]'); // First button
        if (!ivBtn.textContent.includes("invoice") &&  !ivBtn.textContent.includes("Rechnung")) {
            throw new Error("Please switch the web page language to English or German.");
        }

        var dom1 = this.dom.querySelector('div[data-test-id="shipping-section-buyer-address"]'); // Shipment
        var lines = dom1.childNodes
        var dom2 = this.dom.querySelector('table.a-keyvalue'); // orderLines
        var pureLines = [];
        for ( var i=0; i<lines.length; i++ ) {
            pureLines.push(lines[i].textContent.trim());
        }
        pureLines.reverse();
        // Data preprocessing
        const country = pureLines.shift()                           // delete country line.
        const checker = this.checkerMap[country];
        if (checker == undefined) {
            throw new Error("Country is not in the whitelist. [checker]");
        }
        var ele = pureLines[0]
        if (ele.indexOf(",") != -1) {   // if state is not shown
            pureLines.splice(0, 0, ""); // insert state to the array
        }
        if (pureLines.length > 7) {
            throw new Error('Items > 7!');
        }
         // console.log(pureLines);
        
        //en-US: [state], city, zip, street, company, name 
        var shipment = {};
        shipment.country = this.countryWhiteListMap[country];  // Country code
        if (!this.isInCountryWhiteList(shipment.country)) {
            throw new Error(`Country not in the whitelist: [${Object.keys(this.countryWhiteListMap)}]`);
        }

        shipment.state = pureLines[0];
        shipment.city = pureLines[1].replace(',', '');

        const zip = pureLines[2];
        if (!checker.checkZipCode(zip)) {
            throw new Error('ZipCode unrecognized!');
        } else {
            shipment.zip = zip;
        }
    
        const street = pureLines[3];
        if (!checker.checkStreet(street)) {
            throw new Error('Street unrecognized!');
        } else {
            const st = checker.splitStreet(street);
            shipment.street = st[0];
            shipment.houseNumber = st[1];
        }   
        if (pureLines.length == 5) {
            shipment.name1 = pureLines[4];
            shipment.name2 = "";
            shipment.name3 = "";
        } else if (pureLines.length == 6) {
            shipment.name2 = pureLines[4];  // company or c/o
            shipment.name1 = pureLines[5];  // name
            shipment.name3 = "";
        } else if (pureLines.length == 7) {
            shipment.name3 = pureLines[4]; // co
            shipment.name1 = pureLines[5]; // company
            shipment.name2 = pureLines[6]; // name
        }
        if (shipment.name2.toLowerCase().includes("gmbh")) {
            [shipment.name1, shipment.name2] = [shipment.name2, shipment.name1];
        }
        const phoneDom = this.dom.querySelector('span[data-test-id="shipping-section-phone"]');
        const orderLines = this.getOrderLines();
        shipment.phone = phoneDom!=null? phoneDom.textContent : ""
        shipment.email = "";
        shipment.pages = 1;
        shipment.note = this.getNote(orderLines);
        shipment.orderNumber = this.getOrderNumber();
        
        if(this.isDhlParcel(shipment)) {
            throw new Error(`It seems to be a DHL parcel.`); 
        }

        const addrDom = this.dom.querySelector('div[data-test-id="shipping-section-buyer-address"]');

        this.highlight(shipment.name1, addrDom, 'yellow');
        this.highlight(shipment.name2, addrDom, '#FFD700');
        this.highlight(shipment.name3, addrDom, '#EEB422');
        this.highlight(shipment.city, addrDom, '#BEBEBE');
        this.highlight(shipment.zip, addrDom, '#FFDEAD');
        this.highlight(shipment.street, addrDom, '#87CEEB');
        this.highlight(shipment.houseNumber, addrDom, '#54FF9F');
        this.highlight(shipment.state, addrDom, '#F4A460');
        return shipment;
    }

    // Get shipping address from Amazon api
    parseApiData(data) {
        var orderNumber = this.getOrderNumber();
        var address = data[orderNumber].address;
        console.log(address)
        var shipment = {};
        shipment.orderNumber = orderNumber;
        shipment.country = address.countryCode.toLowerCase();   // Country code
        shipment.state = address.stateOrRegion == null? "": address.stateOrRegion;;
        shipment.city = address.city;
        shipment.zip = address.postalCode;

        if (this.isInCountryBlackList(shipment.country.toLowerCase())) {
            throw new Error(`Country is in the blacklist: [${Object.keys(this.countryBlackListMap)}]`);
        }

        var line1 = address.line1 == null? "": address.line1;   // Usually c/o
        var line2 = address.line2 == null? "": address.line2;  // Usually Street and houseNumber
        const checker = new GermanAddrChecker();
        // May fail to recognize the street name and number.
        if (checker.checkStreet(line1)) { 
            [line1, line2] = [line2, line1];
        }
        // line1 could be a streetName when line2 is null.
        if (line2.length == 0) {
            [line1, line2] = [line2, line1];
        }

        var reg = /^[\s\d-/,]+[a-zA-Z]?$/;
        // line1 could be a streetName when line2 is a street number.
        if (reg.test(line2)) {    
            line2 = line1 + " " + line2;
            line1 = "";
        }

        shipment.street = line2;
        shipment.houseNumber = "";
    
        shipment.name1 = address.name == null? "": address.name;
        shipment.name2 = address.companyName == null? "": address.companyName; 
        shipment.name3 = line1; 
        if (shipment.name2.length == 0) {
            [shipment.name2, shipment.name3] = [shipment.name3, shipment.name2];
        }

        if (shipment.name2.toLowerCase().includes("gmbh")) {
            [shipment.name1, shipment.name2] = [shipment.name2, shipment.name1];
        }
        shipment.phone = address.phoneNumber == null? "": address.phoneNumber; 
        shipment.email = "";
        shipment.pages = 1;
        const orderLines = this.getOrderLines();
        shipment.note = this.getNote(orderLines);
        if(this.isDhlParcel(shipment)) {
            throw new Error(`It seems to be a DHL parcel.`); 
        }
        // console.log(shipment);
        return shipment;
    }

    getNote(orderLines) {
        var lines = [];
        for (const o of orderLines) {
            lines.push(`${o.quantity}x[${o.sku}]`);
        }
        return lines.join("\n");
    }

    highlight(keyword, targetDom, color) {
        if (keyword != null ) {
            keyword = keyword.replace("&", "&amp;")
            var content = targetDom.innerHTML;
            var arr = content.split(keyword);
            if (arr.length == 2 ) {
                targetDom.innerHTML = arr.join(`<span style="background:${color};">${keyword}</span>`);
            }
        }
    }

}


export { GermanLike, AmazonApi };



