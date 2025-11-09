import {Button, Dropdown, type MenuProps, Space, Tooltip} from "antd";
import {DownloadOutlined, EditOutlined, FileAddOutlined, MoreOutlined, RocketOutlined, MailOutlined} from "@ant-design/icons";
import {downloadOrderLabel, downloadOrderZip, type OrderResponse} from "@/api/orders.ts";
import SyncTrackingButton from "@/pages/order_fulfillment/components/SyncTrackingButton.tsx";
import {GenerateGlsLabelButton} from "@/pages/order_fulfillment/components/GenerateLabelButton.tsx";
import {OrderStatus} from "@/api/enums.ts";
import UpdateOrderModal from "@/pages/order_fulfillment/components/UpdateOrderModal.tsx";
import {useState} from "react";
import OfaEmailModal from "@/pages/order_fulfillment/components/OfaEmailModal.tsx"

const OrderActions = ({order, onSuccess, onFailure}: {
    order: OrderResponse,
    onSuccess?: () => void,
    onFailure?: (err: any) => void
}) => {
    const [editOrderModalOpen, setOrderModalOpen] = useState(false)
    const [emailModalOpen, setEmailModalOpen] = useState(false)

    const ENABLED_GENERATE_LABEL_STATUSES: OrderStatus[] = [
        OrderStatus.New,
        OrderStatus.LabelFailed,
        OrderStatus.Exception,
    ];

    const ENABLED_SYNC_TRACKING_STATUSES: OrderStatus[] = [
        OrderStatus.LabelCreated,
    ];

    const items: MenuProps['items'] = [
        {
            key: '3',
            label: "订单信息",
            icon: <EditOutlined/>,
            onClick: () => {
                setOrderModalOpen(true)
            }
        },
        {
            key: '4',
            label: '下载面单',
            icon: <DownloadOutlined/>,
            onClick: async () => {
                try {
                    await downloadOrderLabel(order.id)
                } catch (err: any) {
                    console.error(err)
                }
            }
        },
        {
            key: '5',
            label: "下载文档",
            icon: <DownloadOutlined/>,
            onClick: async () => {
                try {
                    await downloadOrderZip(order.id)
                } catch (err: any) {
                    console.error(err)
                }
            }
        },
        {
            key: '6',
            label: "发送邮件",
            icon: <MailOutlined/>,
            onClick: () => {
                setEmailModalOpen(true)
            }
        }

    ]

    return (
        <div>
            {/*{contextHolder}*/}
            <Space>
                <Tooltip title="生成快递单">
                    {<GenerateGlsLabelButton
                        orderId={order.id}
                        type="primary"
                        tooltip={"生成面单"}
                        disabled={!ENABLED_GENERATE_LABEL_STATUSES.includes(order.status)}
                        onSuccess={onSuccess}
                        onFailure={onFailure}
                    >
                        <FileAddOutlined/>
                    </GenerateGlsLabelButton>
                    }
                </Tooltip>
                <SyncTrackingButton
                    orderId={order.id}
                    tooltip={"确认发货并上传跟踪号"}
                    disabled={!ENABLED_SYNC_TRACKING_STATUSES.includes(order.status)}
                    onSuccess={onSuccess}
                    onFailure={onFailure}
                >
                    <RocketOutlined/>
                </SyncTrackingButton>
                <Dropdown
                    menu={{items}}
                >
                    <Button><MoreOutlined/></Button>
                </Dropdown>
            </Space>


            <UpdateOrderModal
                open={editOrderModalOpen}
                onClose={() => setOrderModalOpen(false)}
                orderId={order.id}
                initialValues={{
                    status: order.status,
                    carrier_code: order.carrier_code,
                    parcel_weights: order.parcel_weights,
                    tracking_number: order.tracking_number,
                    tracking_url: order.tracking_url,
                    delivered: order.delivered,
                    seller_note:order.seller_note,
                    estimated_delivery_date: order.estimated_delivery_date,
                }}
                onSuccess={() => {
                    onSuccess?.()
                }}
            >
            </UpdateOrderModal>

            <OfaEmailModal
                open={emailModalOpen}
                onClose={() => setEmailModalOpen(false)}
                order={order}
            />
        </div>
    )

}

export default OrderActions;