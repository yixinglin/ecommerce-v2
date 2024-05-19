# Amazon Order Bulk Processing


### Amazon Bulk Confirmation [Page](src/app/AmazonBulkConfirm.js)
This code can be loaded on the Amazon Bulk Confirmation page. It allows users to copy tracking IDs to the bulk confirmation page with one click.
```
# Examples: 
304-6502205-3216347: ZCBI2OXF
305-8172279-3744300: ZCBI2OXO
306-4009862-1741911: ZCBI2OXP
306-0705206-1681155: ZCBI2OXG
306-6816182-2287526: ZCBI2OXH
306-0734394-8455534: ZCBI2OXI
```

### Amazon Order List [Page](src/app/AmazonOrderList.js)
This code allows users to get a list of unshipped Amazon orders sorted by SKU.

### Build and Run
Copy the code [amazonbulkconfirmmain.js](tm\amazonbulkconfirmmain.js) to temporary monkey. Then run the following commands in the terminal:
```shell
npm install 
# Development build
npm start
# Production build
npm run build 
```