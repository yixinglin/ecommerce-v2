import { Button, Tooltip, message } from 'antd'
import {type ReactNode} from 'react'
import {useGenerateLabel} from "@/hooks/Order.ts";

const external_logistic_id = import.meta.env.VITE_GLS_EXTERNAL_ID

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

export default function GenerateLabelButton (
    { orderId, children, tooltip, size, type, disabled, onSuccess, onFailure }: Props
) {
    const [messageApi, contextHolder] = message.useMessage()
    const { run: generateLabel, loading: confirmGenerateLabelLoading } = useGenerateLabel(messageApi)

    const handleOnClickGenerateLabel = async () => {
        try {
            await generateLabel(orderId, external_logistic_id, false, () => {
                message.info('生成面单成功')
                if (onSuccess) onSuccess()
            }, () => {
                message.error('生成面单失败')
                if (onFailure) onFailure({})
            })
        } catch (error) {
            message.error('生成面单失败')
            console.error(error)
        }
    }

    return (
        <>
            {contextHolder}
            <Tooltip title={tooltip}>
                <Button
                    size={size}
                    type={type}
                    disabled={disabled || confirmGenerateLabelLoading}
                    loading={confirmGenerateLabelLoading}
                    onClick={handleOnClickGenerateLabel}
                >
                    {children}
                </Button>
            </Tooltip>
        </>
    )
}

