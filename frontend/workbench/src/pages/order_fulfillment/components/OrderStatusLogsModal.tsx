import { Table, Modal, Tag } from 'antd'
import type { OrderStatusLog } from '@/api/orders.ts'
import dayjs from 'dayjs'
import {useOrderStatusLogs} from "@/pages/order_fulfillment/hooks.ts";
import {STATUS_COLORS, STATUS_LABELS} from "@/pages/order_fulfillment/components/enums.ts";

interface Props {
    orderId: number
    open: boolean
    onClose: () => void
}

export default function OrderStatusLogsModal({ orderId, open, onClose }: Props) {
    const { logs, loading } = useOrderStatusLogs(orderId)

    const columns = [
        {
            title: '变更时间',
            dataIndex: 'created_at',
            render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm:ss'),
        },
        {
            title: '原状态',
            dataIndex: 'from_status',
            render: (status: string) => {
                const color = STATUS_COLORS[status] || 'default'
                const label = STATUS_LABELS[status] || status
                return   <Tag
                    color={color}
                    style={{
                        fontWeight: 500,
                        borderRadius: 6,
                        padding: '2px 10px',
                    }}
                >
                    {label}
                </Tag>
            }
        },
        {
            title: '变更后状态',
            dataIndex: 'to_status',
            render: (status: string) => {
                const color = STATUS_COLORS[status] || 'default'
                const label = STATUS_LABELS[status] || status
                return  <Tag
                    color={color}
                    style={{
                        fontWeight: 500,
                        borderRadius: 6,
                        padding: '2px 10px',
                    }}
                >
                    {label}
                </Tag>
            },
        },
        {
            title: '备注',
            dataIndex: 'remarks',
            render: (text: string | null) => text || '--',
        }
    ]

    return (
        <Modal
            open={open}
            title="订单状态流转记录"
            onCancel={onClose}
            footer={null}
            width={700}
        >
            <Table<OrderStatusLog>
                rowKey="id"
                loading={loading}
                columns={columns}
                dataSource={logs}
                pagination={false}
                size="middle"
            />
        </Modal>
    )
}

