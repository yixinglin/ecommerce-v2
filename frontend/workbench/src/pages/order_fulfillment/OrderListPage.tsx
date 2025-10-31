import {Button, Col, Form, Input, Modal, Row, Select, Space, Table, Tag, Tooltip, Typography} from 'antd'
import {useEffect, useRef, useState} from 'react'
import {type OrderResponse, update_shipping_tracking_status} from '@/api/orders.ts'
import {ChannelCode, OrderStatus} from '@/api/enums.ts'
import OrderItemList from "@/pages/order_fulfillment/components/OrderItemList.tsx";
import OrderStatusLogsModal from "@/pages/order_fulfillment/components/OrderStatusLogsModal.tsx";
import {getMapUrl} from "@/utils/maps.ts";
import {EnvironmentOutlined, CopyOutlined, ReloadOutlined, SearchOutlined, ClearOutlined} from '@ant-design/icons'
import {OrderAddressModal} from "@/pages/order_fulfillment/components/OrderAddressModal.tsx";
import OrderActions from "@/pages/order_fulfillment/components/OrderActions.tsx";
import {useOrders} from "@/pages/order_fulfillment/hooks.ts";
import {STATUS_COLORS, STATUS_LABELS} from "@/pages/order_fulfillment/components/enums.ts";
import PullOrdersModal from "@/pages/order_fulfillment/components/PullOrdersModal.tsx";
import useMessage from "antd/es/message/useMessage";
import ReactCountryFlag from "react-country-flag"
import {formatTime} from "@/utils/time.ts";
import {useNavigate} from "react-router-dom";
import {CreateBatchButton} from "@/pages/order_fulfillment/components/CreateBatchModal.tsx";
import OrderGuideModalButton from "@/pages/order_fulfillment/components/OrderGuideButton.tsx";


const {Title} = Typography;

const {Option} = Select

const external_gls_id = import.meta.env.VITE_GLS_EXTERNAL_ID


export default function OrderListPage() {
    const [form] = Form.useForm()
    const [messageApi, contextHolder] = useMessage()
    const navigate = useNavigate()

    const {orders, loading, pagination, fetchOrders, refreshOrder, resetOrders} = useOrders({limit: 50, page: 1})

    const [selectedOrderId, setSelectedOrderId] = useState<number | undefined>(undefined)
    const [itemModalVisible, setItemModalVisible] = useState(false)
    const [statusLogModalVisible, setStatusLogModalVisible] = useState(false)
    const [addressModalVisible, setAddressModalVisible] = useState(false)
    const debounceTimer = useRef<number>(0)  // 防抖
    const [isResetting, setIsResetting] = useState(false) // 重置状态锁

    const [pullOrdersModalVisible, setPullOrdersModalVisible] = useState(false)

    useEffect(() => {
        fetchOrders()
    }, [])


    const onSearch = async () => {
        const values = form.getFieldsValue()
        await fetchOrders(values, true)
    }

    const handleReset = async () => {
        setIsResetting(true)
        clearTimeout(debounceTimer.current)
        form.resetFields()
        await resetOrders()  // 调用 Hook 内部的重置逻辑
        setTimeout(() => setIsResetting(false), 500)
    }

    const handleValuesChange = (_: any, allValues: any) => {
        if (isResetting) return // 重置期间不触发防抖请求
        clearTimeout(debounceTimer.current)
        debounceTimer.current = window.setTimeout(() => {
            fetchOrders(allValues, true)
        }, 400)
    }

    const handleUpdateDelivered = async (record: any) => {
        try {
            const res = await update_shipping_tracking_status(
                record.id,
                external_gls_id,
            )
            refreshOrder(record.id)
            messageApi.success('物流状态更新成功')
            console.log(res)
        } catch (e) {
            messageApi.error("物流状态更新失败")
            console.error(e)
        }
    }

    const columns = [
        {title: '序号', dataIndex: 'id', width: 70},
        {
            title: '创建时间',
            dataIndex: 'created_at',
            width: 130,
            render: (value: string) => formatTime(value),
        },
        {
            title: '订单号',
            width: 120,
            dataIndex: 'order_number',
        },
        {
            title: '渠道',
            width: 190,
            dataIndex: 'channel',
            render: (text: string, record: OrderResponse) => (
                <div>
                    <span>{text.toUpperCase()}</span> <br/>
                    店铺: &nbsp;
                    <span style={{color: 'gray'}}>{record.account_id}</span>
                    <span style={{marginLeft: 12}}>
                        <a onClick={() => {
                            navigator.clipboard.writeText(record.account_id || '')
                            messageApi.success('复制成功')
                        }}>
                            <CopyOutlined/>
                        </a>
                    </span>
                </div>
            )

        },
        {
            title: '处理状态',
            dataIndex: 'status',
            width: 110,
            render: (status: string, record: OrderResponse) => {
                const color = STATUS_COLORS[status] || 'default'
                const label = STATUS_LABELS[status] || status
                return (
                    <>
                        <Tooltip title={status} placement="top">
                            <Tag
                                color={color}
                                style={{
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    borderRadius: 6,
                                    padding: '2px 10px',
                                }}
                                onClick={() => {
                                    setSelectedOrderId(record.id)
                                    setStatusLogModalVisible(true)
                                }}
                            >
                                {label}
                            </Tag>
                        </Tooltip>
                    </>
                )
            },
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
                    {record.customer_note &&<span><br/><span style={{color: 'red'}}>买家留言: &nbsp;{record.customer_note}</span></span>  }
                </div>)
            }

        },
        {
            title: '国家',
            dataIndex: 'country_code',
            width: 90,
            render: (text: string) => (
                <>
                    <ReactCountryFlag
                        countryCode={text}
                        svg
                        style={{width: "1.5em", height: "1.5em"}}
                    />
                    <span style={{marginLeft: 8}}>{text}</span>
                </>
            )
        },
        {
            title: '追踪号',
            dataIndex: 'tracking_number',
            width: 200,
            ellipsis: true,
            render: (text: string, record: OrderResponse) => (
                <div>
                    <span>
                        <Tooltip title={record.tracking_info || '暂无物流信息'}>
                            <a href={record?.tracking_url || ''} target="_blank" rel="noopener noreferrer"> {text} </a>
                        </Tooltip>
                    </span> <br/>
                    {record.batch_id && (
                            <span
                                style={{color: 'gray', fontSize: 9, cursor: 'pointer'}}
                                onClick={() => {
                                    navigate(`/batches`, {})
                                }}
                            >
                                {record.batch_id}
                            </span>
                    )}<br/>

                    {record.delivered && <Tag color="blue">客户已收货</Tag>  }
                    {!record.delivered
                        &&
                            <Button
                                type="link"
                                onClick={
                                    () => {
                                        handleUpdateDelivered(record)
                                    }
                                }
                            >
                                查询到货状态
                            </Button>
                    }
                </div>
            )
        },
        {
            title: '图片',
            dataIndex: 'thumbnails',
            width: 290,
            render: (text: string, record: OrderResponse) => {
                const urls: string[] = text.split(',').slice(0, 4)
                return (
                    <>
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
                        <div>
                            <span>{record.parcel_weights} (kg)</span>
                        </div>
                    </>
                )
            }
        },
        {
            title: '操作',
            render: (record: OrderResponse) => (
                <OrderActions
                    order={record}
                    onSuccess={() => refreshOrder(record.id)}
                    onFailure={() => refreshOrder(record.id)}
                />
            ),
        }
    ]

    return (
        <div style={{padding: 24}}>
            {contextHolder}

            <Row justify="space-between" align="middle" style={{marginBottom: 16}}>
                <Col>
                    <Title level={4}>📋 订单处理系统</Title>
                </Col>
                <Col>
                    <Space>
                        <Button icon={<ReloadOutlined/>} type="primary" onClick={() => setPullOrdersModalVisible(true)}>拉取订单</Button>
                        <CreateBatchButton
                            tooltip={'注意：所有【已确认发货】的订单将会被合并到同一个批次中，供集中下载。'}
                        >
                            生成订单批次
                        </CreateBatchButton>
                        <Button icon={<SearchOutlined/>} onClick={() => navigate('/batches', {})}>
                            查看批次
                        </Button>

                    </Space>
                </Col>
            </Row>


            <Form
                form={form}
                layout="inline"
                onFinish={onSearch}
                onValuesChange={handleValuesChange}
            >
                <Form.Item name="status" label="状态">
                    <Select allowClear style={{width: 120}}>
                        {Object.values(OrderStatus).map((key) => (
                            <Option key={key} value={key}>{STATUS_LABELS[key] || key}</Option>
                        ))}
                    </Select>
                </Form.Item>
                <Form.Item name="channel_code" label="渠道">
                    <Select allowClear style={{width: 140}}>
                        <Option value={ChannelCode.WooCommerce}>WooCommerce</Option>
                        <Option value={ChannelCode.Amazon}>Amazon</Option>
                    </Select>
                </Form.Item>
                <Form.Item name="delivered" label="已收货">
                    <Select allowClear style={{width: 90}}>
                        <Option value={true}>是</Option>
                        <Option value={false}>否</Option>
                    </Select>
                </Form.Item>
                <Form.Item name="keyword" label="搜索词">
                    <Input placeholder="请输入搜索词"/>
                </Form.Item>
                <Form.Item>
                    <Button icon={<SearchOutlined/>} type="primary" htmlType="submit" loading={loading}>查询</Button>
                </Form.Item>
                <Form.Item>
                    <Button icon={<ClearOutlined/>} onClick={handleReset}>重置</Button>
                </Form.Item>
                <Form.Item>
                    <OrderGuideModalButton />
                </Form.Item>
            </Form>

            <Table
                dataSource={orders}
                loading={loading}
                pagination={pagination}
                columns={columns}
                rowKey="id"
            />

            {
                selectedOrderId && (
                    <Modal
                        title="订单商品详情"
                        open={itemModalVisible}
                        onCancel={() => setItemModalVisible(false)}
                        footer={null}
                        width={800}
                    >
                        {itemModalVisible && <OrderItemList orderId={selectedOrderId}/>}
                    </Modal>
                )
            }

            {selectedOrderId && (
                statusLogModalVisible && <OrderStatusLogsModal
                    orderId={selectedOrderId}
                    open={statusLogModalVisible}
                    onClose={() => setStatusLogModalVisible(false)}
                />
            )}

            {selectedOrderId && (
                addressModalVisible && <OrderAddressModal
                    orderId={selectedOrderId}
                    open={addressModalVisible}
                    onClose={() => setAddressModalVisible(false)}
                />
            )}

            {
                <PullOrdersModal
                    open={pullOrdersModalVisible}
                    onClose={() => setPullOrdersModalVisible(false)}
                    onSuccess={() => {
                        // 拉取成功后刷新订单列表
                        fetchOrders()
                    }}
                />

            }

        </div>
    )
}



