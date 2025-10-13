import {Form, message, Modal, Select} from 'antd'
import {useState} from 'react'
import {type OrderUpdatePayload, updateOrder} from "@/api/orders.ts";
import {useOrderEnums} from "@/pages/order_fulfillment/context.tsx";


interface Props {
    open: boolean
    onClose: () => void
    orderId: number
    initialValues?: OrderUpdatePayload
    onSuccess?: () => void
}

export default function UpdateOrderModal({
                                             open,
                                             onClose,
                                             orderId,
                                             initialValues,
                                             onSuccess,
                                         }: Props) {
    const [form] = Form.useForm()
    const [loading, setLoading] = useState(false)
    const [messageApi, contextHolder] = message.useMessage()
    const { enums } = useOrderEnums()

    const handleOk = async () => {
        try {
            const values = await form.validateFields()
            setLoading(true)
            await updateOrder(orderId, values)
            messageApi.success('订单更新成功')
            onSuccess?.()
            onClose()
        } catch (err: any) {
            messageApi.error(err?.response?.data?.detail || '更新失败')
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            {contextHolder}
            <Modal
                open={open}
                title="编辑订单"
                onCancel={onClose}
                onOk={handleOk}
                confirmLoading={loading}
                destroyOnClose
            >
                <Form form={form} layout="vertical" initialValues={initialValues}>
                    <Form.Item name="status" label="订单状态">
                        <Select allowClear options={enums?.order_status} placeholder="请选择订单状态"/>
                    </Form.Item>
                    <Form.Item name="carrier_code" label="承运商">
                        <Select allowClear options={enums?.carrier_code} placeholder="请选择承运商"/>
                    </Form.Item>
                </Form>
            </Modal>
        </>
    )
}

