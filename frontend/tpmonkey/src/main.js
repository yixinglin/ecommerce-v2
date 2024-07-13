import AmazonBulkConfirm from './app/AmazonBulkConfirm.js';
import AmazonOrderList from './app/AmazonOrderList.js';


var bc = new AmazonBulkConfirm();
bc.mount();
var ol = new AmazonOrderList();
ol.mount();
