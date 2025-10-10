import { Button, message, Tooltip } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import { useState } from 'react'
import {downloadBatchZip} from "@/api/orders.ts";


interface Props {
    batchId: string,
    disabled?: boolean,
    tooltip?: string,
    onSuccess?: () => void,
}

export default function DownloadBatchButton({ batchId, disabled, tooltip, onSuccess }: Props) {
    const [loading, setLoading] = useState(false)
    const [messageApi, contextHolder] = message.useMessage()

    const handleDownload = async () => {
        try {
            setLoading(true)
            await downloadBatchZip(batchId)
            onSuccess?.()
            messageApi.success('文件下载成功')
        } catch (err: any) {
            messageApi.error(err.message || '下载失败')
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            {contextHolder}
            <Tooltip title={tooltip}>
                <Button
                    loading={loading}
                    onClick={handleDownload}
                    disabled={disabled}
                >
                    <DownloadOutlined />
                </Button>
            </Tooltip>
        </>
    )
}
