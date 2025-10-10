import {Modal, Spin, Descriptions, Card, Button, message} from 'antd'
import { useOrderAddress } from '@/hooks/Order'
import type { OrderAddress } from '@/api/orders'
import { CopyOutlined } from '@ant-design/icons'

interface CardProps {
    title: string
    address: OrderAddress
}

export function AddressCard({ title, address }: CardProps) {
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
                title={title}
                extra={
                    <Button type="link" icon={<CopyOutlined />} onClick={handleCopy}>
                        复制地址
                    </Button>
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

interface OaProps {
    orderId: number
    open: boolean
    onClose: () => void
}

export function OrderAddressModal({ orderId, open, onClose }: OaProps) {
    const shipping = useOrderAddress(orderId, 'shipping')
    const billing = useOrderAddress(orderId, 'billing')
    return (
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
                    <AddressCard title="收货地址" address={shipping.address!} />
                    <AddressCard title="账单地址" address={billing.address!} />
                </>
            )}
        </Modal>
    )
}
