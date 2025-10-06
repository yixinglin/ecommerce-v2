import { postForm, get } from '@/utils/http'

interface LoginParams {
    username: string
    password: string
}

export const login = (data: LoginParams) => {
    return postForm('/api/v1/login', data)
}

export const getUserInfo = () =>
     get('/api/v1/userinfo')


