import {Table, Tag, Card, Button, Space} from 'antd'
import { EyeOutlined } from '@ant-design/icons'
import { useRequest } from '@/hooks/useRequest'
import { useEffect } from 'react'
import {type BatchResponse, listBatches, type ListResponse} from "@/api/orders.ts";
import {batchStatusColors} from "@/pages/order_fulfillment/components/enums.ts";
import {formatTime} from "@/utils/time.ts";
import CompleteBatchButton from "@/pages/order_fulfillment/components/CompleteBatchButton.tsx";
import {BatchStatus} from "@/api/enums.ts";
import DownloadBatchButton from "@/pages/order_fulfillment/components/DownloadBatchButton.tsx";

export default function BatchListPage() {
    const {
        data,
        loading,
        run: fetchBatches,
    } = useRequest<ListResponse<BatchResponse>>(listBatches, {
        manual: true,
        defaultParams: { page: 1, limit: 10 },
    })

    useEffect(() => {
        fetchBatches()
    }, [])

    const columns = [
        {
            title: "创建日期",
            dataIndex: "created_at",
            render: (value: string) => formatTime(value),
            width: 150,
        },
        {
            title: '批次号',
            dataIndex: 'batch_id',
        },
        {
            title: '订单数',
            width: 100,
            dataIndex: 'order_count',
        },
        {
          title: "下载次数",
          width: 100,
          dataIndex: 'download_count',
        },
        {
            title: '状态',
            dataIndex: 'status',
            width: 100,
            render: (status: string) => (
                <Tag color={batchStatusColors[status] || 'default'}>
                    {status.toUpperCase()}
                </Tag>
            ),
        },
        {
            title: '操作人',
            dataIndex: 'operator',
        },
        {
            title: '操作',
            key: 'action',
            render: (_: any, record: BatchResponse) => (
                <Space>
                    <DownloadBatchButton
                        batchId={record.batch_id}
                        tooltip={'下载批次'}
                        onSuccess={() => {
                            fetchBatches?.()
                        }}
                    />
                    <CompleteBatchButton
                        batchId={record.batch_id}
                        disabled={record.status === BatchStatus.Completed || record.download_count == 0}
                        onSuccess={() => {
                            fetchBatches?.()
                        }}
                    />
                    <Button
                        onClick={() => console.log('TODO: 查看详情', record.batch_id)}
                    >
                        <EyeOutlined />
                    </Button>
                </Space>
            ),
        },
    ]

    return (
        <Card title="📦 订单批次列表" style={{ margin: 24 }}>
            <Table
                rowKey="id"
                loading={loading}
                dataSource={data?.data || []}
                columns={columns}
                pagination={{
                    current: data?.page || 1,
                    pageSize: data?.limit || 10,
                    total: data?.total || 0,
                    showQuickJumper: true,
                    showSizeChanger: true,
                    onChange: (page, limit) => {
                        fetchBatches({ page, limit })
                    },
                }}
            />
        </Card>
    )
}


