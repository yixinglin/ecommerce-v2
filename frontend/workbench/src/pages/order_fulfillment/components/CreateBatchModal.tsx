import {Modal, Form, Select, Input, message, Button, Tooltip} from 'antd'
import {type ReactNode, useState} from 'react'

import {useAuth} from "@/hooks/useAuth.ts";
import {useEnums} from "@/pages/order_fulfillment/hooks.ts";
import {createBatch} from "@/api/orders.ts";
import {useNavigate} from "react-router-dom";
import {PaperClipOutlined} from "@ant-design/icons";

interface Props {
    open: boolean
    onClose: () => void
    onSuccess?: (batchId: string) => void
}

export default function CreateBatchModal({ open, onClose, onSuccess }: Props) {
    const { user } = useAuth()
    const [form] = Form.useForm()
    const [loading, setLoading] = useState(false)
    const [messageApi, contextHolder] = message.useMessage()
    const { enums, loading: enumsLoading } = useEnums()

    const handleOk = async () => {
        try {
            const values = await form.validateFields()
            setLoading(true)
            const res = await createBatch(values)
            messageApi.success(`创建成功，批次号：${res.batch_id}`)
            onSuccess?.(res.batch_id)
            onClose()
        } catch (err: any) {
            if (err?.errorFields) return
            messageApi.error(err?.response?.data?.detail || err?.message || '创建失败')
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            {contextHolder}
            <Modal
                open={open}
                onCancel={onClose}
                onOk={handleOk}
                confirmLoading={loading}
                title="生成订单批次"
                okText="创建"
            >
                <p style={{ color: 'orange' }}> 注意：确认【发货】之后才能创建订单发货【批次】  </p>
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="channel_code"
                        label="渠道"
                        rules={[{ required: true, message: '请选择渠道' }]}
                    >
                        <Select
                            placeholder="请选择渠道"
                            loading={enumsLoading}
                            allowClear
                            options={enums?.channel_codes || []}
                        />
                    </Form.Item>

                    <Form.Item name="account_id" label="账号 ID">
                        <Input placeholder="可选：填写账号 ID" />
                    </Form.Item>

                    <Form.Item
                        name="operator" label="操作人"
                        rules={[{ required: true, message: '请选择操作人' }]}
                    >
                        <Input placeholder={user?.alias} />
                    </Form.Item>
                </Form>
            </Modal>
        </>
    )
}

interface  PropsButton {
    children?: ReactNode,
    tooltip?: string,
    size?: 'small' | 'middle' | 'large'
    type?: 'primary' | 'default' | 'link' | 'text',
}

export function CreateBatchButton({
    children, tooltip, size, type} : PropsButton
) {
    const [open, setOpen] = useState(false)
    const navigate = useNavigate()
    return (
        <>
            <Tooltip title={tooltip}>
                <Button
                    type={type}
                    icon={<PaperClipOutlined/>}
                    onClick={() => setOpen(true)}
                    size={size}
                >
                    {/*创建订单批次*/}
                    {children}
                </Button>
            </Tooltip>
            <CreateBatchModal
                open={open}
                onClose={() => setOpen(false)}
                onSuccess={(batchId) => {
                    console.log('创建成功，批次号：', batchId)
                    alert(`创建成功，批次号：${batchId}. 即将跳转到下载页。`)
                    // 可以在这里刷新批次列表，或跳转到详情页
                    navigate('/batches')
                }}
            />
        </>
    )
}
