import { Table, Modal, Tag } from 'antd'
import type { OrderStatusLog } from '@/api/orders.ts'
import dayjs from 'dayjs'
import {useOrderStatusLogs} from "@/hooks/Order.ts";
import {OrderStatus} from "@/api/enums.ts";

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
            render: (status: string | null) =>
                status ? (
                    <Tag color={getOrderStatusColor(status)}>
                         {status}
                    </Tag>
                ) : (
                    <Tag>无</Tag>
                ),
        },
        {
            title: '变更后状态',
            dataIndex: 'to_status',
            render: (status: string) => (
                <Tag color={getOrderStatusColor(status)}>
                     {status}
                </Tag>
            ),
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

export function getOrderStatusColor(status: string): string {
    switch (status) {
        case OrderStatus.New:
            return 'gold'
        case OrderStatus.WaitingLabel:
        case OrderStatus.LabelCreated:
        case OrderStatus.Uploaded:
            return 'processing'
        case OrderStatus.Synced:
        case OrderStatus.Completed:
            return 'green'
        case OrderStatus.LabelFailed:
        case OrderStatus.SyncFailed:
        case OrderStatus.UploadFailed:
        case OrderStatus.Exception:
            return 'red'
        case OrderStatus.Cancelled:
            return 'default'
        default:
            return 'blue'
    }
}
