import { appendButton, setValueToInputElm,  waitForElm} from '../utils/utilsui.js';
import { GermanLike, AmazonApi } from './components/amazon_order.js';
import { getCatalogAttributes } from '../rest/amazon.js'
// import { Carriers } from '../rest/gls.js';
import {createGlsLabel, getGlsShipmentsByReference, getGlsShipmentsViewByReference, displayGlsLabel} from '../rest/gls.js';


class AmazonOrderDetails {

    constructor(baseurl) {
        console.log('AmazonOrderDetails constructor');
        this.baseurl = baseurl;
        this.mountPoint = 'div[data-test-id="order-details-header-action-buttons"]'
        this.catalogAttributes = {};
        this.orderLines = null;
        this.weight = 0;
    }


    mount() {
        waitForElm(this.mountPoint).then(() => {
            console.log('AmazonOrderDetails mounted');
            this.extractor = new GermanLike(document);
            this.orderLines = this.extractor.getOrderLines();
            this.createButton(1);
            return this.fetchCatalogAttributes();
        })            
    }

    createButton(index) {
        if(index == 1) {
            appendButton('识别地址[1]','extract-button',  this.mountPoint, 
                () => this.onClickExtractButton());   
        } else if(index == 2) {
            appendButton('GLS[2]', 'gls-button', this.mountPoint, 
                () => this.onClickGLSButton());  
        } else if(index == 3) {
            appendButton('直接打印[3]', 'one-click-button', this.mountPoint, 
                () => {this.onClickOneClickButton()});  
        }    
    }

    fetchCatalogAttributes() {
        console.log('fetchCatalogAttribute111');
        const asins = this.orderLines.map(line => line.asin);
        getCatalogAttributes(asins).then(res => {            
            const data = JSON.parse(res.responseText).data;    
            this.catalogAttributes = data.catalog_attributes;
            console.log(this.catalogAttributes);
        }).catch(err => {
            console.error(err);
        });
    }

    // 1. Button to extract shipment details
    onClickExtractButton() {
        console.log('onClickExtractOrderDetails');
        var shipment = null;
        try {
            shipment = this.extractor.parseFromWebSurface();
            if (shipment) {
                const info = JSON.stringify(shipment, null, 2);
                this.createButton(2);
                var gls_btn = document.querySelector("#extract-button");
                gls_btn.disabled = true;
            }                
        } catch (err) {
            alert(err);
            this.createButton(3);
        }
        console.log(shipment);
        this.shipment = shipment;
    }

    // 2. Gls button to create parcel labels.
    onClickGLSButton() {        
        this.createGlsLabel(this.shipment);
    }

    // 3. Apply Amazon API to create GLS label.
    onClickOneClickButton() {
        var shipment = null;
        AmazonApi.fetchShipmentFromApi(this.extractor.getOrderNumber())
        .then(res => {            
            var shipment = JSON.parse(res.responseText);
            shipment = this.extractor.parseApiData(shipment);
            if (shipment != undefined) {
                this.createGlsLabel(shipment)
            }
        }).catch(err => {
            alert(err);
        });
        console.log(shipment);
    }

    // 原始的createGlsLabel方法 v2024
    // createGlsLabel(shipment) {
    //     Carriers.createGlsLabel(this.baseurl+'/gls/label', shipment, (trackId) => {
    //         console.log(trackId);
    //         let trackInput = document.querySelector('input[data-test-id="text-input-tracking-id"]');
    //         if (trackInput) {
    //             setValueToInputElm(trackInput, trackId);
    //         }
    //     });
    // }

    calculateWeight(orderLines) {
        var weight = 0;
        const dimMap = {};
        for(const a of this.catalogAttributes) {
            dimMap[a.asin] = a.package_dimensions;
        }
        orderLines.forEach(line => {                        
            const w = dimMap[line.asin].weight;
            weight += line.quantity * w / 1000;
        });
        return weight;
    }

    createGlsLabel(shipment) {
        var weight = 1;
        try {            
            weight = this.calculateWeight(this.orderLines);
        } catch (err) {
            console.error(err);
            alert("Failed to calculate weight. Please check the catalog attributes.");
        }

        var shipment2 = {
            "consignee": {
              "name1": shipment.name1,
              "name2": shipment.name2,
              "name3": shipment.name3,
              "street1": shipment.street.trim() + " " + shipment.houseNumber,
              "zipCode": shipment.zip,
              "city": shipment.city,
              "province": shipment.state,
              "country": shipment.country,
              "email": shipment.email,
              "telephone": shipment.phone,
              "mobile": shipment.phone,
            },
            "parcels": [
              {
                "weight": weight,
                "comment": "",
                "content": ""
              },
            ],
            "references": [
              shipment.orderNumber,
            ]
        }
        console.log(shipment2)

        var reference = null;
        createGlsLabel(shipment2).then(resp => {      
            // Create a GLS label.          
            const text = JSON.parse(resp.responseText);        
            console.log(text);
            reference = text.data.id;
            return getGlsShipmentsByReference(reference);        
        }).then((resp) => {        
            // Fill out the tracking number in the input field.
            const shipments = JSON.parse(resp.responseText).data;
            const shipment = shipments[0];
            var parcelNumber = shipment.parcels[0].parcelNumber;                                
            let trackInput = document.querySelector('input[data-test-id="text-input-tracking-id"]');
            if (trackInput) {
                setValueToInputElm(trackInput, parcelNumber);
            }
            return getGlsShipmentsViewByReference(reference);       
        }).then((resp) => {
            // Open the GLS label in a new window.
            displayGlsLabel(resp.responseText);
        }).catch(resp => {
            console.error(resp.responseText);            
            Toast("Error", 1000)
        })
    }

}

export default AmazonOrderDetails;