import EmailButton from "@/components/EmailButton.tsx";
import { Modal, Space, Typography } from "antd";
import templates from "@/assets/ofa_email_templates.json"
import Mustache from "mustache";
import {type OrderResponse} from '@/api/orders.ts'
import {formatDate} from "@/utils/time.ts";


const { Text } = Typography;

interface EmailButtonProps
{
    order: OrderResponse;
    open: boolean;
    onClose: () => void;
}

export default function OfaEmailModal({
    order,
    open,
    onClose,
}: EmailButtonProps) {
    const placeholders = {
        "order_number": order.order_number? order.order_number: "[Bestellnummer]",
        "tracking_number": order.tracking_number? order.tracking_number: "[Bestellnummer]",
        "tracking_url": order.tracking_url? order.tracking_url: "[Bestellnummer]",
        "estimated_delivery_date": order.estimated_delivery_date? formatDate(order.estimated_delivery_date): "[Datum]"
    }


    return (
        <Modal
            title="邮件模板"
            open={open}
            onCancel={onClose}
            footer={null}
            centered
        >
            <Text type="secondary">
                请选择邮件模板并发送给客户
            </Text>

            <div style={{ marginTop: 16 }}>
                <Space direction="vertical" style={{ width: "100%" }}>
                    {templates.map((tpl, index) => (
                        <EmailButton
                            key={index}
                            to={""}
                            subject={tpl.subject}
                            body={Mustache.render(tpl.body, placeholders)}
                            label={tpl.label}
                            type="link"
                        />
                    ))}
                </Space>
            </div>
        </Modal>
    );
};

