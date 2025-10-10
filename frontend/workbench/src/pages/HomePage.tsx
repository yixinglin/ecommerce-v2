
import { Button, Avatar } from 'antd'
import Cookies from 'js-cookie'
import {useAuth} from "@/hooks/useAuth.ts";

export default function HomePage() {
    const { user, setUser } = useAuth()

    const logout = () => {
        Cookies.remove('token')
        localStorage.removeItem('token')
        setUser(null)
        window.location.href = '/login'
    }

    if (!user) return <div>正在加载...</div>

    return (
        <div style={{ padding: 30 }}>
            <h1>欢迎回来，{user.alias || user.username}</h1>
            <Avatar src={user.avatar} size={64} />
            <p>用户名: {user.username}</p>
            <p>性别: {user.gender == 0? '男' : '女'}</p>
            <p>手机号: {user.phone}</p>
            <p>Email: {user.email}</p>
            <p>地址: {user.address}</p>
            <p>签名: {user.signature}</p>
            <p>生日: {user.birthday}</p>
            <div style={{ marginTop: 20 }}>
                <Button onClick={logout}>退出登录</Button>
            </div>
        </div>
    )
}
