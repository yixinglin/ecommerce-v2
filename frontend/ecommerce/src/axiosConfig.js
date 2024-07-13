// src/axiosConfig.js
import axios from 'axios';



// 创建一个 Axios 实例
const api = axios.create({
  baseURL: 'http://localhost:5018', // 设置默认的域名
  timeout: 10000, // 设置请求超时时间
  headers: {
    'Content-Type': 'application/json',
    // 其他默认的头部信息
  }
});

// 可以添加请求拦截器
api.interceptors.request.use(
  config => {
    // 在请求发送之前可以做些什么
    return config;
  },
  error => {
    // 处理请求错误
    return Promise.reject(error);
  }
);

// 可以添加响应拦截器
api.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response;
  },
  error => {
    // 处理响应错误
    return Promise.reject(error);
  }
);

export default api;
