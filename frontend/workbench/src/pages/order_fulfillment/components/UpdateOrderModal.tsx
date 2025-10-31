import {Form, Input, message, Modal, Select} from 'antd'
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
                    <Form.Item
                        name="parcel_weights"
                        label="包裹重量"
                        tooltip={{
                            title: "包裹重量, 逗号隔开, 单位: 千克(kg). 例如: 1.2,1.4,2.5",
                        }}
                        rules={[
                            { required: false, message: "请输入包裹重量" },
                            {
                                pattern: /^[0-9,.\s]+$/,
                                message: "只能输入数字, 英文逗号, 小数点(句号)",
                            },
                        ]}
                    >
                        <Input placeholder="请输入包裹重量"/>
                    </Form.Item>
                </Form>
            </Modal>
        </>
    )
}

