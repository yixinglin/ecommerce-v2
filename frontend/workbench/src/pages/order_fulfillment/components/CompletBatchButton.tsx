import { Button, message, Popconfirm } from 'antd'
import { useState } from 'react'
import { CheckSquareOutlined } from '@ant-design/icons'
import {completeBatch} from "@/api/orders.ts";

interface Props {
    batchId: string
    disabled?: boolean
    onSuccess?: () => void
}

export default function CompleteBatchButton({ batchId, disabled, onSuccess }: Props) {
    const [loading, setLoading] = useState(false)
    const [messageApi, contextHolder] = message.useMessage()

    const handleComplete = async () => {
        try {
            setLoading(true)
            const res = await completeBatch(batchId)
            if (res.success) {
                messageApi.success('批次已成功完成')
                onSuccess?.()
            }
        } catch (err: any) {
            messageApi.error(err?.response?.data?.detail || '完成失败')
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            {contextHolder}
            <Popconfirm
                title="确定要完成此批次？"
                description={'点击确认后，与之关联的所有订单将被标记为已完成。'}
                onConfirm={handleComplete}
                okText="确定"
                cancelText="取消"
            >
                <Button
                    type="primary"
                    disabled={disabled}
                    loading={loading}
                >
                    <CheckSquareOutlined />
                </Button>
            </Popconfirm>
        </>
    )
}
