import {Modal, Spin, Descriptions, Card, Button, message, Form, Input} from 'antd'
import { useOrderAddress } from '@/pages/order_fulfillment/hooks.ts'
import {getOrderAddress, type OrderAddress, updateOrderAddress} from '@/api/orders'
import { CopyOutlined, EditOutlined } from '@ant-design/icons'
import {useEffect, useState} from "react";

interface CardProps {
    title: string
    address: OrderAddress
    onEdit?: () => void
}

export function AddressCard({ title, address, onEdit }: CardProps) {
    const [ messageApi, contextHolder ] =  message.useMessage()

    const handleCopy = () => {
        const lines = [
            address.company,
            address.name,
            address.address1,
            address.address2,
            `${address.postal_code} ${address.city}`,
            address.state_or_province,
            address.country_code,
            address.phone,
            address.mobile,
            address.email,
        ].filter(Boolean)
        const fullText = lines.join('\n')
        navigator.clipboard.writeText(fullText)
            .then(() => messageApi.success('Copied to clipboard'))
            .catch(() => messageApi.error('复制失败'))
    }

    const descriptionItems = [
        { label: "公司", value: address?.company },
        { label: "姓名", value: address?.name },
        { label: "街道", value: address?.address1 },
        { label: "附加信息", value: address?.address2 },
        { label: "邮编 / 城市", value: `${address?.postal_code} ${address?.city}` },
        { label: "省/州", value: address?.state_or_province },
        { label: "国家", value: address?.country_code },
        { label: "手机", value: address?.mobile },
        { label: "邮箱", value: address?.email },
        { label: "电话", value: address?.phone },
    ];

    return (
        <>
            {contextHolder}
            <Card
                title={`${title} [${address?.id}]` }
                extra={
                    <>
                        <Button type="link" icon={<CopyOutlined />} onClick={handleCopy}>
                            复制地址
                        </Button>
                        {onEdit && ( // 编辑按钮
                            <Button type="link" icon={<EditOutlined />} onClick={onEdit}>
                                编辑
                            </Button>
                        )}
                    </>
                }
                size="small"
                style={{ marginBottom: 16 }}
            >
                <Descriptions
                    column={1} size="small" bordered
                >
                    {descriptionItems
                        .filter((item) => item.value) // 只保留非空字段
                        .map((item) => (
                            <Descriptions.Item key={item.label} label={item.label}>
                                {item.value}
                            </Descriptions.Item>
                        ))}
                </Descriptions>
            </Card>
        </>
    )
}

// 新增：编辑 Shipping Address 的弹窗
interface EditAddressModalProps {
    open: boolean
    orderId: number
    initialValues?: OrderAddress
    onClose: () => void
    onSuccess: () => void
}

function EditAddressModal({ open, orderId, initialValues, onClose, onSuccess }: EditAddressModalProps) {
    const [form] = Form.useForm()
    const [saving, setSaving] = useState(false)
    const [messageApi, contextHolder] = message.useMessage()

    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            setSaving(true)
            await updateOrderAddress(orderId, 'shipping', values)
            messageApi.success('收货地址已更新')
            onSuccess?.() // ✅ 通知父组件刷新或更新
            onClose()
        } catch (err) {
            messageApi.error('更新失败')
            console.error(err)
        } finally {
            setSaving(false)
        }
    }

    return (
        <>
            {contextHolder}
            <Modal
            open={open}
            title="编辑收货地址"
            onCancel={onClose}
            onOk={handleSubmit}
            okText="保存"
            confirmLoading={saving}
        >
            <Form form={form} layout="vertical" initialValues={initialValues}>
                <Form.Item name="company" label="公司"><Input /></Form.Item>
                <Form.Item name="name" label="姓名" rules={[{ required: true, message: '请输入姓名' }]}><Input /></Form.Item>
                <Form.Item name="address1" label="街道" rules={[{ required: true, message: '请输入街道' }]}><Input /></Form.Item>
                <Form.Item name="address2" label="附加信息"><Input /></Form.Item>
                <Form.Item name="postal_code" label="邮编"><Input /></Form.Item>
                <Form.Item name="city" label="城市"><Input /></Form.Item>
                <Form.Item name="state_or_province" label="省/州"><Input /></Form.Item>
                <Form.Item name="country_code" label="国家代码"><Input /></Form.Item>
                {/*<Form.Item name="mobile" label="手机"><Input /></Form.Item>*/}
                {/*<Form.Item name="email" label="邮箱"><Input /></Form.Item>*/}
                {/*<Form.Item name="phone" label="电话"><Input /></Form.Item>*/}
            </Form>
        </Modal>
        </>

    )
}

interface OaProps {
    orderId: number
    open: boolean
    onClose: () => void
}

export function OrderAddressModal({ orderId, open, onClose }: OaProps) {
    const shipping = useOrderAddress(orderId, 'shipping')
    const billing = useOrderAddress(orderId, 'billing')

    // 本地保存 shipping 地址副本
    const [shippingAddress, setShippingAddress] = useState<OrderAddress | null>(null)
    const [editOpen, setEditOpen] = useState(false)

    useEffect(() => {
        if (shipping.address) {
            setShippingAddress(shipping.address)
        }
    }, [shipping.address])

    const handleSuccess = async () => {
        const updated = await getOrderAddress(orderId, 'shipping')
        setShippingAddress(updated)
    }

    return (
        <>
            <Modal
                open={open}
                title="客户地址"
                onCancel={onClose}
                footer={null}
                width={800}
            >
                {shipping.loading || billing.loading ? (
                    <Spin />
                ) : (
                    <>
                        <AddressCard
                            title="收货地址"
                            address={shippingAddress!}
                            onEdit={() => setEditOpen(true)} // 新增
                        />
                        <AddressCard title="账单地址" address={billing.address!} />
                    </>
                )}
            </Modal>
            <EditAddressModal
                open={editOpen}
                orderId={orderId}
                initialValues={shippingAddress ?? undefined}
                onClose={() => setEditOpen(false)}
                onSuccess={handleSuccess}
            />
        </>

    )
}
