import {Button, Dropdown, type MenuProps, Tooltip} from "antd";
import {MoreOutlined, PlayCircleOutlined} from "@ant-design/icons";
import type {OrderStatus} from "@/api/enums.ts";

type OrderActionsProps = {
    orderId: number,
    status: OrderStatus
}

const OrderActions = ({orderId, status}: OrderActionsProps) => {
    const items: MenuProps['items'] = [
        {
            key: '1',
            label: "查看订单项",
            icon: <PlayCircleOutlined />,
            onClick: () => {
                // console.log("查看订单项")
                alert("查看订单项")
            }
        }
    ]

    return (
        <div>
            <Tooltip title="处理订单">
                <Button type="primary">
                    <PlayCircleOutlined />
                </Button>
            </Tooltip>
            <Tooltip title="生成快递单">
                <Button type="default">
                    生成快递单
                </Button>
            </Tooltip>
            <Tooltip title="确认发货">
                <Button type="default">
                    确认发货
                </Button>
            </Tooltip>
            <Dropdown
                menu={{items }}
            >
                <Button><MoreOutlined /></Button>
            </Dropdown >
        </div>
    )

}

export default OrderActions;