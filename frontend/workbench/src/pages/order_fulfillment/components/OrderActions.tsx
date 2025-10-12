import {Button, Dropdown, type MenuProps, Space, Tooltip} from "antd";
import {EditOutlined, FileAddOutlined, MoreOutlined, RocketOutlined} from "@ant-design/icons";
import {type OrderResponse} from "@/api/orders.ts";
import SyncTrackingButton from "@/pages/order_fulfillment/components/SyncTrackingButton.tsx";
import GenerateLabelButton from "@/pages/order_fulfillment/components/GenerateLabelButton.tsx";
import {OrderStatus} from "@/api/enums.ts";
import UpdateOrderModal from "@/pages/order_fulfillment/components/UpdateOrderModal.tsx";
import {useState} from "react";

// const external_logistic_id = import.meta.env.VITE_GLS_EXTERNAL_ID

const OrderActions = ({order, onSuccess, onFailure}: {
    order: OrderResponse,
    onSuccess?: () => void,
    onFailure?: (err: any) => void
}) => {

    // const [ contextHolder] = message.useMessage()
    const [editOrderModalOpen, setOrderModalOpen] = useState(false)

    const ENABLED_GENERATE_LABEL_STATUSES: OrderStatus[] = [
        OrderStatus.New,
        OrderStatus.LabelFailed,
        OrderStatus.Exception,
    ];

    const ENABLED_SYNC_TRACKING_STATUSES: OrderStatus[] = [
        OrderStatus.LabelCreated,
    ];

    // const handleOrderChange = () => {
    //     cancelOrder(order.id).then(() => {
    //         onSuccess?.();
    //         messageApi.success("订单取消成功");
    //     }).catch((err) => {
    //         onFailure?.(err);
    //         messageApi.error("订单取消失败");
    //     })
    // }

    const items: MenuProps['items'] = [
        {
            key: '3',
            label: "修改订单信息",
            icon: <EditOutlined/>,
            onClick: () => {
                setOrderModalOpen(true)
            }
        }
    ]

    return (
        <div>
            {/*{contextHolder}*/}
            <Space>
                <Tooltip title="生成快递单">
                    {<GenerateLabelButton
                        orderId={order.id}
                        type="primary"
                        tooltip={"生成面单"}
                        disabled={!ENABLED_GENERATE_LABEL_STATUSES.includes(order.status)}
                        onSuccess={onSuccess}
                        onFailure={onFailure}
                    >
                        <FileAddOutlined/>
                    </GenerateLabelButton>
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
                }}
                onSuccess={() => {
                    onSuccess?.()
                }}
            >
            </UpdateOrderModal>

        </div>
    )

}

export default OrderActions;