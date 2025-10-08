import {Routes, Route} from 'react-router-dom'
import HomePage from './pages/HomePage.tsx'
import Login from './pages/user/Login.tsx'
import './App.css'

import {PrivateRoute} from "@/components/PrivateRoute.tsx";
import NavigationBar from "@/components/NavigationBar.tsx";
import OrderFulfillment from "@/pages/order_fulfillment/OrderFulfillment.tsx";

function App() {
    console.log('当前环境:', import.meta.env.MODE);
    console.log('接口地址:', import.meta.env.VITE_API_BASE_URL);
    return (
        <div style={{padding: 20}}>
            <NavigationBar/>

            <Routes>
                <Route path="/login" element={<Login/>}/>
                <Route path="/about" element={<HomePage/>}/>
                <Route path="/orders" element={<OrderFulfillment/>}/>

                <Route
                    path="/"
                    element={
                        <PrivateRoute>
                            <HomePage/>
                        </PrivateRoute>
                    }
                />
            </Routes>
        </div>

    )
}

export default App
