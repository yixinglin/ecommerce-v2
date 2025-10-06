import { Routes, Route, Link, Navigate  } from 'react-router-dom'
import HomePage from './pages/HomePage.tsx'
import Login from './pages/user/Login.tsx'


import './App.css'
import type {JSX} from "react"
import {useAuth} from "@/hooks/useAuth.ts";

function PrivateRoute({ children }: { children: JSX.Element }) {
    const { user } = useAuth()
    if (!user && !localStorage.getItem('token')) {
        return <Navigate to="/login" replace />
    }
    return children
}

function App() {
    console.log('当前环境:', import.meta.env.MODE);
    console.log('接口地址:', import.meta.env.VITE_API_BASE_URL);
  return (    
    <div style={{ padding: 20 }}>      
      <nav>
        <Link to="/">首页</Link> |{' '}
        <Link to="/about">关于</Link>
      </nav>

      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<HomePage />} />

          <Route
              path="/"
              element={
                  <PrivateRoute>
                      <HomePage />
                  </PrivateRoute>
              }
          />
      </Routes>
  </div>

  )
}

export default App
