import { Modal, Form, Select, Input, message } from 'antd'
import { useState } from 'react'
import { pullOrders, type PullOrdersPayload } from '@/api/orders'
import {useEnums} from "@/hooks/Order.ts";

const { Option } = Select

interface Props {
    open: boolean
    onClose: () => void
    onSuccess?: () => void
}

export default function PullOrdersModal({ open, onClose, onSuccess }: Props) {
    const [form] = Form.useForm()
    const [loading, setLoading] = useState(false)
    const [messageApi, contextHolder] = message.useMessage()
    const { enums } = useEnums()

    const handleOk = async () => {
        try {
            const values = await form.validateFields()
            setLoading(true)
            const res = await pullOrders(values as PullOrdersPayload)
            messageApi.success(`拉取成功，共 ${res.success_count} 条`)
            onSuccess?.()
            onClose()
        } catch (err: any) {
            if (err?.errorFields) return // 表单校验错误
            messageApi.error(err?.response?.data?.detail || err?.message || '拉取失败')
        } finally {
            setLoading(false)
        }
    }

    // TODO: 选择渠道之后，拉取账号信息


    return (
        <>
            {contextHolder}
            <Modal
                open={open}
                onCancel={onClose}
                onOk={handleOk}
                title="拉取订单"
                confirmLoading={loading}
                okText="开始拉取"
                cancelText="取消"
                width={250}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="channel_code"
                        label="渠道"
                        rules={[{ required: true, message: '请选择渠道' }]}
                    >
                        <Select placeholder="请选择渠道" allowClear style={{ width: 200 }}>
                            {enums?.channel_codes.map((item) => (
                                <Option key={item.value} value={item.value}>
                                    {item.label}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="account_id"
                        label="账号 ID"
                        rules={[{ required: true, message: '请输入账号 ID' }]}
                    >
                        <Input placeholder="请输入账号 ID" style={{ width: 200 }} />
                    </Form.Item>
                </Form>
            </Modal>
        </>
    )
}
