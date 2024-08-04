import { appendButton, setValueToInputElm,  waitForElm} from '../utils/utilsui.js';
import { GermanLike, AmazonApi } from './components/amazon_order.js';
import { Carriers } from '../rest/gls.js';


class AmazonOrderDetails {

    constructor(baseurl) {
        console.log('AmazonOrderDetails constructor');
        this.baseurl = baseurl;
        this.mountPoint = 'div[data-test-id="order-details-header-action-buttons"]'
    }


    mount() {
        waitForElm(this.mountPoint).then(() => {
            console.log('AmazonOrderDetails mounted');
            this.extractor = new GermanLike(document);
            this.createButton(1);
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

    createGlsLabel(shipment) {
        Carriers.createGlsLabel(this.baseurl+'/gls/label', shipment, (trackId) => {
            console.log(trackId);
            let trackInput = document.querySelector('input[data-test-id="text-input-tracking-id"]');
            if (trackInput) {
                setValueToInputElm(trackInput, trackId);
            }
        });
    }

}

export default AmazonOrderDetails;