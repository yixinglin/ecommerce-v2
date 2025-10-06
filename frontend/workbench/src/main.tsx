import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import 'antd/dist/reset.css'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import {AuthProvider} from "@/context/AuthProvider.tsx";


ReactDOM.createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
    <ConfigProvider locale={zhCN}>  
      {/* 可以配置主题色 */}
        <AuthProvider>
            <App />
        </AuthProvider>
    </ConfigProvider>
      
    </BrowserRouter>
  </StrictMode>,
)
