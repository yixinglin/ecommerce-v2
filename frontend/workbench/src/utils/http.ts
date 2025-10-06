import axios, {type AxiosRequestConfig} from 'axios'
import { message } from 'antd'
import Cookies from 'js-cookie'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 20000,
})

// 请求拦截器
http.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token') || Cookies.get('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// 响应拦截器
http.interceptors.response.use(
    (res) => res.data,
    (error) => {
        if (error.response?.status === 401) {
            message.error('登录已过期，请重新登录')
            Cookies.remove('token')
            localStorage.removeItem('token')
            window.location.href = '/login'
        } else {
            message.error(error.response?.data?.message || '请求失败')
        }
        return Promise.reject(error)
    }
)

/**
 * 便捷方法封装：get / post
 */
export function get<T = any>(
    url: string,
    config?: AxiosRequestConfig
): Promise<T> {
    return http.get<any, T>(url, config)
}

export function post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
): Promise<T> {
    return http.post<any, T>(url, data, config)
}

// 提交 form-data 的方法
export const postForm = (url: string, data: Record<string, any>) => {
    const form = new URLSearchParams()
    Object.keys(data).forEach((key) => form.append(key, data[key]))
    return post(url, form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
}

export default http
