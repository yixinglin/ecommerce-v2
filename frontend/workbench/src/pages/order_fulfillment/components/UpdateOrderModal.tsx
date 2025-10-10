import {Form, message, Modal, Select} from 'antd'
import {useState} from 'react'
import {type OrderUpdatePayload, updateOrder} from "@/api/orders.ts";
import {useEnums} from "@/hooks/Order.ts";

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
    const {enums} = useEnums()

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

// interface  PropsButton {
//     order: OrderResponse,
//     children?: ReactNode,
//     tooltip?: string,
//     size?: 'small' | 'middle' | 'large'
//     type?: 'primary' | 'default' | 'link' | 'text',
//     onSuccess?: () => void,
//     onFailure?: () => void,
// }

// export function UpdateOrderButton({
//     order, children, tooltip, size, type, onSuccess
// }: PropsButton) {
//     const [editOpen, setEditOpen] = useState(false)
//     return <>
//         <Tooltip title={tooltip}>
//             <Button
//                 type={type}
//                 size={size}
//                 onClick={() => setEditOpen(true)}>
//                 {children || '编辑订单'}
//             </Button>
//         </Tooltip>
//
//         <UpdateOrderModal
//             open={editOpen}
//             onClose={() => setEditOpen(false)}
//             orderId={order.id}
//             initialValues={{
//                 status: order.status,
//                 carrier_code: order.carrier_code,
//             }}
//             onSuccess={() => {onSuccess?.()}}
//         >
//         </UpdateOrderModal>
//     </>
// }