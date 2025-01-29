import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import ProductView from './views/ProductView'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* <App /> */}
    <ProductView />
  </StrictMode>,
)
