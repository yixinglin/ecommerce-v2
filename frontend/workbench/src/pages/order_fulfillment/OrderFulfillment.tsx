import {Table, Input, Select, Form, Button, Modal} from 'antd'
import {useEffect, useState} from 'react'
import {useRequest} from '@/hooks/useRequest'
import {listOrders, type ListResponse, type OrderQuery, type OrderResponse} from '@/api/orders.ts'
import {OrderStatus, ChannelCode} from '@/api/enums.ts'
import dayjs from 'dayjs'
import OrderItemList from "@/pages/order_fulfillment/components/OrderItemList.tsx";
import OrderStatusLogsModal from "@/pages/order_fulfillment/components/OrderStatusLogsModal.tsx";
import {getMapUrl} from "@/utils/maps.ts";
import {EnvironmentOutlined} from '@ant-design/icons'
import {OrderAddressModal} from "@/pages/order_fulfillment/components/OrderAddressModal.tsx";
import OrderActions from "@/pages/order_fulfillment/components/OrderActions.tsx";

const {Option} = Select

export default function OrderList() {
    const [form] = Form.useForm()
    const [selectedOrderId, setSelectedOrderId] = useState<number | undefined>(undefined)
    const [itemModalVisible, setItemModalVisible] = useState(false)
    const [statusLogModalVisible, setStatusLogModalVisible] = useState(false)
    const [addressModalVisible, setAddressModalVisible] = useState(false)

    const {
        data,
        loading,
        run: fetchOrders,
    } = useRequest<ListResponse<OrderResponse>, OrderQuery>(listOrders, {
        manual: true,
        defaultParams: {page: 1, limit: 10}, // 初始加载
    })

    useEffect(() => {
        fetchOrders()
    }, [])

    const onSearch = () => {
        const values = form.getFieldsValue()
        fetchOrders(values)
    }

    const columns = [
        {title: 'ID', dataIndex: 'id'},
        {
            title: '创建时间',
            dataIndex: 'created_at',
            render: (value: string) => dayjs(value).format('DD.MM.YYYY HH:mm'),
        },
        {
            title: '订单号',
            dataIndex: 'order_number'
        },
        {
            title: '渠道',
            dataIndex: 'channel',
            render: (text: string, record: OrderResponse) => (
                <div>
                    <span>{text.toUpperCase()}</span> <br/>
                    <span style={{color: 'gray'}}>{record.account_id}</span>
                </div>
            )

        },
        {
            title: '处理状态',
            dataIndex: 'status',
            render: (text: string, record: OrderResponse) => (
                <a
                    onClick={() => {
                        setSelectedOrderId(record.id)
                        setStatusLogModalVisible(true)
                    }}
                >
                    {text.toUpperCase()}
                </a>
            ),
        },
        {
            title: '买家 / 地址',
            dataIndex: 'buyer_name',
            render: (text: string, record: OrderResponse) => {
                const fullAddress = `${record.buyer_address || ''}, ${record.country_code || ''}`.trim()
                const mapUrl = getMapUrl(fullAddress)
                return (<div>
                    <span>
                            <a
                                onClick={() => {
                                    setSelectedOrderId(record.id)
                                    setAddressModalVisible(true)
                                }}
                            >
                                {text}
                        </a>
                    </span> <br/>
                    <span style={{color: 'gray'}}>{record.buyer_address}</span>
                    {mapUrl && (
                        <a
                            href={mapUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{marginLeft: 8}}
                            title="在地图中查看"
                        >
                            <EnvironmentOutlined/>
                        </a>
                    )}
                </div>)
            }

        },
        {title: '国家', dataIndex: 'country_code'},
        {title: '追踪号', dataIndex: 'tracking_number'},
        {
            title: '图片',
            dataIndex: 'thumbnails',
            render: (text: string, record: OrderResponse) => {
                const urls: string[] = text.split(',').slice(0, 4)
                return (
                    <div
                        style={{cursor: 'pointer'}}
                        onClick={() => {
                            setSelectedOrderId(record.id)
                            setItemModalVisible(true)
                        }}
                    >
                        {urls.map((url, index) => (
                            <img key={index} src={url} style={{width: 50, height: 50, margin: 5}}/>
                        ))}
                    </div>
                )
            }
        },
        {
            title: '操作',
            render: (record: OrderResponse) => (
                <OrderActions
                    orderId={record.id}
                    status={record.status}
                />
            ),
        }
    ]

    return (
        <div style={{padding: 24}}>
            <Form form={form} layout="inline" onFinish={onSearch}>
                <Form.Item name="status" label="状态">
                    <Select allowClear style={{width: 120}}>
                        {Object.values(OrderStatus).map((key) => (
                            <Option key={key} value={key}>{key}</Option>
                        ))}
                    </Select>
                </Form.Item>
                <Form.Item name="channel_code" label="渠道">
                    <Select allowClear style={{width: 140}}>
                        {Object.values(ChannelCode).map((code) => (
                            <Option key={code} value={code}>{code}</Option>
                        ))}
                    </Select>
                </Form.Item>
                <Form.Item name="account_id" label="账号">
                    <Input placeholder="请输入账号"/>
                </Form.Item>
                <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>查询</Button>
                </Form.Item>
            </Form>

            <Table
                style={{marginTop: 20}}
                rowKey="id"
                loading={loading}
                dataSource={data?.data || []}
                columns={columns}
                pagination={{
                    current: data?.page || 1,
                    pageSize: data?.limit || 10,
                    total: data?.total || 0,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    onChange: (page, limit) => {
                        const values = form.getFieldsValue()
                        fetchOrders({...values, page, limit})
                    },
                    hideOnSinglePage: false,
                }}
            />

            <Modal
                title="订单商品详情"
                open={itemModalVisible}
                onCancel={() => setItemModalVisible(false)}
                footer={null}
                width={800}
            >
                {selectedOrderId && <OrderItemList orderId={selectedOrderId}/>}
            </Modal>

            {selectedOrderId && (
                <OrderStatusLogsModal
                    orderId={selectedOrderId}
                    open={statusLogModalVisible}
                    onClose={() => setStatusLogModalVisible(false)}
                />
            )}

            {selectedOrderId && (
                <OrderAddressModal
                    orderId={selectedOrderId}
                    open={addressModalVisible}
                    onClose={() => setAddressModalVisible(false)}
                />
            )}

        </div>
    )
}
