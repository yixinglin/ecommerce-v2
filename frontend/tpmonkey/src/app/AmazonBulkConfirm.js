import { waitForElm, setValueToInputElm, listen_ctrl_key_event } from '../utils/utilsui.js';

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
    waitForElm(this.mountPoint).then(() => {
      alert("Press Ctrl+I to fill all track id edit boxes");
      listen_ctrl_key_event('i', (event) => {
        navigator.clipboard.readText().then(text => {                
            const trackIdMap = this.getTrackIdMap(text);
            this.fillAllTrackIdEditBox(trackIdMap);
        }).catch(err => {
          alert("Failed to read clipboard contents: " + err);
        });

      })
    })
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

  getTrackIdMap(text) {    
    text = text.trim();    
    const lines = text.split('\n');    
    const trackIdMap = {};
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      console.log(line);
      const [orderId, trackId] = line.split(':');
      console.log(orderId, trackId);
      trackIdMap[orderId.trim()] = trackId.trim();
    }
    return trackIdMap;
  }

  fillAllTrackIdEditBox(trackIdMap) {
    const orderIds = this.findAllOrderIds();
    const trackIdEditBox = this.findAllTrackIdEditBox();
    const refs = orderIds.join(';');
    const trackIdBoxMap = {};
    for (let i = 0; i < trackIdEditBox.length; i++) {
      const id = orderIds[i];
      const trackId = trackIdMap[id];
      if (trackId) {
        setValueToInputElm(trackIdEditBox[i], trackId);
      }
    }
  }

}

export default AmazonBulkConfirm;