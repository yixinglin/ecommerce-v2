import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import ProductListView from './views/ProductListView'
import ProductView from "./views/ProductView"; // 新增产品详情页
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
    <Router>
      <Routes>
        <Route path="/" element={<ProductListView />} />
        <Route path="/product/:id" element={<ProductView />} /> {/* 动态路由 */}
      </Routes>
    </Router>

    </>
  )
}

export default App
