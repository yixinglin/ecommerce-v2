import {Navigate} from 'react-router-dom'
import type {JSX} from "react";
import {useAuth} from "@/hooks/useAuth.ts";
import Cookies from "js-cookie";

// 路由守卫
// 如果 token 不存在，跳转到 /login；
export const PrivateRoute = ({children}: { children: JSX.Element }) => {
    const {user} = useAuth()
    const token = localStorage.getItem('token') || Cookies.get('token')
    if (!token && !user) {
        return <Navigate to="/login" replace/>
    }
    return children
}