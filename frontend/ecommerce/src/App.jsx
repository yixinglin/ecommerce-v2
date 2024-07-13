import AmazonOrderList from "./components/OrderList/AmazonOrderList"
import { BrowserRouter, Route, Routes,   } from 'react-router-dom';
import AmazonBulkShipment from "./components/OrderList/AmazonBulkShipment"
import ShipmentForm from "./components/Shipment/ShipmentForm";

import { postShipmentForm, downloadShipmentLabel } from "./components/Shipment/restapi.js";

function App() {
  
  async function handleSubmit(data) {
    const resp = await postShipmentForm(data);
    // const {code, data_, message} = resp.data;
    return resp.data
  }

  return (
    <>
      <BrowserRouter>
          <Routes>
            <Route>
              <Route path="/" exact element={<AmazonOrderList/>} />
              <Route path="/bulk-shipment" exact element={<AmazonBulkShipment/>} />
              <Route path="/shipment-form" exact element={<ShipmentForm carrierName={"GLS"} handleSubmit={handleSubmit}  />} />
            </Route>
          </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
