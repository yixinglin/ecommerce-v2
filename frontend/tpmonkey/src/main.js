import AmazonBulkConfirm from './app/AmazonBulkConfirm';
import AmazonOrderList from './app/AmazonOrderList';


var bc = new AmazonBulkConfirm();
var ol = new AmazonOrderList();
ol.mount();
bc.mount();