import { useState, useCallback } from 'react'
import { message } from 'antd'
// import http from '@/utils/http.ts'

interface RequestOptions<TParams> {
  manual?: boolean // 是否手动触发
  onSuccess?: (data: any) => void
  onError?: (err: any) => void
  defaultParams?: TParams
}

export function useRequest<TData = any, TParams = any>(
  apiFunc: (params?: TParams) => Promise<TData>,
  options: RequestOptions<TParams> = {}
) {
  const { manual = false, onSuccess, onError, defaultParams } = options
  const [data, setData] = useState<TData | null>(null)
  const [loading, setLoading] = useState(!manual)

  const run = useCallback(
    async (params?: TParams) => {
      try {
        setLoading(true)
        const result = await apiFunc(params ?? defaultParams)
        setData(result)
        onSuccess?.(result)
      } catch (err) {
        onError?.(err)
        message.error('Request failed')
      } finally {
        setLoading(false)
      }
    },
    [apiFunc, onSuccess, onError, defaultParams]
  )

  // 自动执行
  if (!manual && !data && !loading) {
    run(defaultParams)
  }

  return { data, loading, run }
}

// TODO: 全局 Token 刷新
// 在 response.interceptors 中处理 401


// import { Button, Spin, Card } from 'antd'
// import { getUserInfo } from './api/user'
// import { useRequest } from './api/useRequest'

// export default function App() {
//   const { data, loading, run } = useRequest(getUserInfo, { manual: true })

//   return (
//     <div style={{ padding: 40 }}>
//       <Card title="用户信息" style={{ maxWidth: 400 }}>
//         <Button type="primary" onClick={() => run()} disabled={loading}>
//           获取用户信息
//         </Button>

//         <div style={{ marginTop: 20 }}>
//           {loading ? (
//             <Spin />
//           ) : (
//             data && (
//               <pre style={{ background: '#f5f5f5', padding: 10 }}>
//                 {JSON.stringify(data, null, 2)}
//               </pre>
//             )
//           )}
//         </div>
//       </Card>
//     </div>
//   )
// }
