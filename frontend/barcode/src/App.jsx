import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import ProductListView from './views/ProductListView'
import ProductView from "./views/ProductView"; // 新增产品详情页
import StockListView from './views/StockListView'
import ProductPackagingListView from './views/ProductPackagingListView'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
    <Router>
      <Routes>
        <Route path="/" element={<ProductListView />} />
        <Route path="/product/:id" element={<ProductView />} /> {/* 动态路由 */}
        <Route path="/stock/:product_id" element={<StockListView />} />
        <Route path="/product/:product_id/packaging" element={<ProductPackagingListView />} />
      </Routes>
    </Router>

    </>
  )
}

export default App
