
class AmazonBulkConfirm {
  /* 
    App applied to the Amazon Bulk Confirm page
  */
  constructor() {
    console.log(`AmazonBulkConfirm constructor`);
    this.mountPoint = ".a-column.a-span12.a-text-right.a-span-last";
  }

  toLoad() {
    if (!document.querySelector('#bulk-confirm-orders-table')) {
      return false;
    } else {
      return true;
    }
  }

  mount() {
    if (!this.toLoad()) {
      console.log('Not Amazon Bulk Confirm page');
      return;
    }
    this.appendButton1();
    this.fillAllTrackIdEditBox();

  }

  findAllTrackIdEditBox() {
    const trackIdEditBox = document.querySelectorAll('input[data-test-id="text-input-tracking-id"]');    
    return trackIdEditBox;
  }

  findAllOrderIds() {
    var orderIds = document.querySelectorAll('td:nth-child(1) > div > div.cell-body-title > a');
    orderIds = [...orderIds].map(item => item.textContent);
    return orderIds;
  }

  fillAllTrackIdEditBox() {
    const orderIds = this.findAllOrderIds();
    const trackIdEditBox = this.findAllTrackIdEditBox();
    const refs = orderIds.join(';');
    
    // for (let i = 0; i < orderIds.length; i++) {
    //   trackIdEditBox[i].value = trackId;
    // }
  }

  appendButton1() {
    // 批量打印gls单子
    console.log('appendButton1');
  }

  appendButton2() {
    // 打印当前页面的拣货单
  }

  appendButton3() {
    // 保存csv文件
  }
}

export default AmazonBulkConfirm;