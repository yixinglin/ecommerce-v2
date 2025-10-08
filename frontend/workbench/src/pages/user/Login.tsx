import {useNavigate} from 'react-router-dom'
import {Form, Input, Button, Card, message, Checkbox} from 'antd'
import {login, getUserInfo} from '@/api/user'

import Cookies from 'js-cookie'
import {useAuth} from "@/hooks/useAuth.ts";

export default function Login() {
    const [form] = Form.useForm()
    const navigate = useNavigate()
    const {setUser} = useAuth()
    const [messageApi, contextHolder] = message.useMessage();

    const handleLogin = async () => {
        try {
            const {username, password, remember} = await form.validateFields()
            const res = await login({username, password})
            const token = res.access_token

            if (token) {
                // localStorage.setItem('token', token)

                if (remember) {
                    Cookies.set('token', token, {expires: 7}) // 7 天有效
                } else {
                    // localStorage.setItem('token', token) // 当前会话
                    Cookies.set('token', token, {expires: 7}) // 7 天有效
                }

                console.log("登录成功")
                messageApi.info('登录成功！')

                const user = await getUserInfo()
                setUser(user)
                navigate('/') // 登录成功跳转首页
            }
        } catch (err: any) {
            console.log("登录失败")
            messageApi.error(err?.response?.data?.message || '登录失败')
        }
    }

    return (
        <div
            style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh',
                background: '#f0f2f5',
            }}
        >
            {contextHolder}
            <Card title="用户登录" style={{width: 350}}>
                <Form form={form} layout="vertical">
                    <Form.Item
                        label="用户名"
                        name="username"
                        rules={[{required: true, message: '请输入用户名'}]}
                    >
                        <Input placeholder="Username"/>
                    </Form.Item>

                    <Form.Item
                        label="密码"
                        name="password"
                        rules={[{required: true, message: '请输入密码'}]}
                    >
                        <Input.Password placeholder="Password"/>
                    </Form.Item>

                    <Form.Item name="remember" valuePropName="checked" initialValue={true}>
                        <Checkbox>记住我</Checkbox>
                    </Form.Item>

                    <Form.Item>
                        <Button type="primary" block onClick={handleLogin}>
                            登录
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    )
}
