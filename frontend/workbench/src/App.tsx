import {Routes, Route} from 'react-router-dom'
import HomePage from './pages/HomePage.tsx'
import Login from './pages/user/Login.tsx'
import './App.css'

import {PrivateRoute} from "@/components/PrivateRoute.tsx";
import NavigationBar from "@/components/NavigationBar.tsx";
import OrderFulfillment from "@/pages/order_fulfillment/OrderListPage.tsx";
import BatchListPage from "@/pages/order_fulfillment/BatchListPage.tsx";
import EmailListPage from "@/pages/reply_handler/EmailListPage.tsx";

function App() {
    console.log('当前环境:', import.meta.env.MODE);
    console.log('接口地址:', import.meta.env.VITE_API_BASE_URL);
    return (
        <div style={{padding: 20}}>
            <NavigationBar/>

            <Routes>
                <Route path="/login" element={<Login/>}/>
                <Route path="/about" element={<HomePage/>}/>
                <Route path="/batches" element={<BatchListPage/>} />
                <Route path="/orders" element={
                    <PrivateRoute>
                        <OrderFulfillment/>
                    </PrivateRoute>
                }/>
                <Route path="/reply_handler" element={
                    <PrivateRoute>
                        <EmailListPage/>
                    </PrivateRoute>
                }/>

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
