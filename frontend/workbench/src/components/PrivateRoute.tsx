import {Navigate} from 'react-router-dom'
import type {JSX} from "react";
import {useAuth} from "@/hooks/useAuth.ts";

// 路由守卫
// 如果 token 不存在，跳转到 /login；
export const PrivateRoute = ({children}: { children: JSX.Element }) => {
    const {user} = useAuth()
    if (!user && !localStorage.getItem('token')) {
        return <Navigate to="/login" replace/>
    }
    return children
}