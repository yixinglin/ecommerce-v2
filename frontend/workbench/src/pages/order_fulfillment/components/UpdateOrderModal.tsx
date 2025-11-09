import {DatePicker, Form, Input, message, Modal, Select, Switch} from 'antd'
import {useState} from 'react'
import {type OrderUpdatePayload, updateOrder} from "@/api/orders.ts";
import {useOrderEnums} from "@/pages/order_fulfillment/context.tsx";
import dayjs from "dayjs";


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

            // 格式化日期
            const formattedValues = {
                ...values,
                estimated_delivery_date: values.estimated_delivery_date?.format('YYYY-MM-DD'),
            }

            setLoading(true)
            await updateOrder(orderId, formattedValues)
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
                <Form form={form}
                      layout="vertical"
                      initialValues={{
                          ...initialValues,
                          estimated_delivery_date: initialValues?.estimated_delivery_date
                          ? dayjs(initialValues?.estimated_delivery_date)
                          : null,
                      }}
                >
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
                    <Form.Item
                        name="tracking_number"
                        label="运单号"
                        tooltip={{
                            title: "运单号, 例如: 1234567890",
                        }}
                    >
                        <Input placeholder="请输入运单号"/>
                    </Form.Item>
                    <Form.Item
                        name="tracking_url"
                        label="运单链接"
                        tooltip={{
                            title: "运单链接, 例如: https://www.example.com/tracking/1234567890",
                        }}
                    >
                        <Input placeholder="请输入运单链接"/>
                    </Form.Item>
                    <Form.Item
                        name="seller_note"
                        label="商家备注"
                        tooltip={{
                            title: "商家备注, 例如: 请注意包裹质量",
                        }}
                    >
                        <Input.TextArea placeholder="请输入商家备注"/>
                    </Form.Item>
                    <Form.Item
                        name="estimated_delivery_date"
                        label="预计到货日期"
                    >
                        <DatePicker
                            format="DD.MM.YYYY"
                            disabledDate={(current) => current && current < dayjs().startOf('day')}
                            placeholder="请选择预计到货日期"
                            style={{ width: '100%' }}
                        />
                    </Form.Item>
                    <Form.Item
                        name="delivered"
                        label="是否已发货"
                        valuePropName="checked"
                        tooltip={{
                            title: "是否已发货",
                        }}
                    >
                        <Switch />
                    </Form.Item>
                </Form>
            </Modal>
        </>
    )
}

