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

