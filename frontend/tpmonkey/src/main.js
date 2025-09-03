import AmazonBulkConfirm from './app/AmazonBulkConfirm.js';
import AmazonOrderList from './app/AmazonOrderList.js';
import AmazonOrderDetails from './app/AmazonOrderDetails.js';
import EbayOrderDetails from './app/EbayOrderDetails.js';
import VipOrderDetails from './app/VipOrderDetails.js';
import VipCustomerAccount from './app/VipCustomerAccount.js';

function applications() {
    console.log("Welcome to TPMonkey");
    var bc = new AmazonBulkConfirm();
    bc.mount();
    var ol = new AmazonOrderList();
    ol.mount();

    const gls_host = GLS_HOST;
    const base_url = BASE_URL;
    var od = new AmazonOrderDetails(gls_host);    
    od.mount();
    var ed = new EbayOrderDetails(gls_host);
    ed.mount();

    var vd = new VipOrderDetails(base_url);
    vd.mount();

    VipCustomerAccount();
    
}

applications();



