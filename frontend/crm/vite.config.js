import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // host: '192.168.8.70', // 允许局域网访问
    host: 'localhost', // 允许局域网访问
    port: 5173, // 你可以修改端口
    strictPort: true,
  }
})
