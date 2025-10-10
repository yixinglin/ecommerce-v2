import { Button, Tooltip, message } from 'antd'
import {type ReactNode, useState} from 'react'
import { syncTrackingInfo } from '@/api/orders'

interface Props {
    orderId: number
    children?: ReactNode
    tooltip?: string
    size?: 'small' | 'middle' | 'large'
    type?: 'primary' | 'default' | 'link' | 'text',
    disabled?: boolean
    onSuccess?: () => void,
    onFailure?: (err: any) => void,
}

export default function SyncTrackingButton(
    { orderId, children, tooltip, size, type = 'default', disabled,onSuccess, onFailure }: Props
) {
    const [loading, setLoading] = useState(false)
    const [messageApi, contextHolder] = message.useMessage()

    const handleSync = async () => {
        try {
            setLoading(true)
            const res = await syncTrackingInfo(orderId)
            if (res.success) {
                messageApi.success('同步追踪信息成功')
                onSuccess?.()
            } else {
                messageApi.error('同步失败')
                onFailure?.({})
            }
        } catch (err: any) {
            messageApi.error(err?.response?.data?.detail || err?.message || '同步失败')
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            {contextHolder}
            <Tooltip title={tooltip}>
                <Button
                    size={size}
                    type={type}
                    loading={loading}
                    disabled={disabled}
                    onClick={handleSync}
                >
                    {children ?? '同步追踪'}
                </Button>
            </Tooltip>
        </>
    )
}
