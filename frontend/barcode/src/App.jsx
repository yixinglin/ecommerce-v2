import { useState } from 'react'
import './App.css'
import ProductListView from './views/ProductListView'
import ProductView from "./views/ProductView"; // 新增产品详情页
import StockListView from './views/StockListView'
import ProductPackagingListView from './views/ProductPackagingListView'
import DeliveryOrderForm from './views/DeliveryOrderForm'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import NavBar from './components/NavBar'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>    
    <Router>
      <NavBar />
      <Routes>
        <Route path="/products" element={<ProductListView />} />
        <Route path="/product/:id" element={<ProductView />} /> {/* 动态路由 */}
        <Route path="/stock/:product_id" element={<StockListView />} />
        <Route path="/product/:product_id/packaging" element={<ProductPackagingListView />} />
        <Route path="/delivery-order" element={<DeliveryOrderForm />} />
      </Routes>
    </Router>

    </>
  )
}

export default App
