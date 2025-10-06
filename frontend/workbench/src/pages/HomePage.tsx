
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
            <p>Email: {user.email}</p>
            <Avatar src={user.avatar} size={64} />
            <div style={{ marginTop: 20 }}>
                <Button onClick={logout}>退出登录</Button>
            </div>
        </div>
    )
}
