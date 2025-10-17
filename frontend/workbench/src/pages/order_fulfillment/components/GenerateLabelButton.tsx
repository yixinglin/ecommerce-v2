import { Button, Tooltip, message } from 'antd'
import {type ReactNode, useState} from 'react'
import {generateLabel} from "@/api/orders.ts";

const external_gls_id = import.meta.env.VITE_GLS_EXTERNAL_ID

interface Props {
    orderId: number
    children?: ReactNode
    tooltip?: string
    size?: 'small' | 'middle' | 'large'
    type?: 'primary' | 'default' | 'link' | 'text',
    disabled?: boolean,
    onSuccess?: () => void,
    onFailure?: (err: any) => void,
}

export function GenerateGlsLabelButton (
    { orderId, children, tooltip, size, type, disabled, onSuccess, onFailure }: Props
) {
    const [messageApi, contextHolder] = message.useMessage()
    const [loading, setLoading] = useState(false)

    const handleOnClickGenerateLabel = async () => {
        try {
            setLoading(true)
            const res = await generateLabel(orderId, external_gls_id, false)
            if (res?.success) {
                messageApi.success('快递单生成成功')
                onSuccess?.()
            } else {
                messageApi.error('生成快递单失败，请查看历史日志详情！')
                console.error(res)
                onFailure?.({})
            }
        } catch (error: any) {
            messageApi.error('生成快递单失败，请查看历史日志详情！')
            messageApi.error(error?.response?.data?.detail || error?.message || '生成失败')
            console.error(error)
            onFailure?.({})
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
                    disabled={disabled || loading}
                    loading={loading}
                    onClick={handleOnClickGenerateLabel}
                >
                    {children}
                </Button>
            </Tooltip>
        </>
    )
}