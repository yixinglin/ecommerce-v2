import {useState} from "react";
import EmailProcessModal from "@/pages/reply_handler/components/EmailProcessModal.tsx";
import {Button, Space, Tooltip} from "antd";
import type {EmailResponse} from "@/api/emails.ts";
import useMessage from "antd/es/message/useMessage";
import EmailActionHistoryModal from "@/pages/reply_handler/components/EmailActionHistoryModal.tsx";
import {EditOutlined, HistoryOutlined} from "@ant-design/icons";

interface Props {
    email: EmailResponse;
    onSuccess?: () => void;
    onFailure?: (error: any) => void;
}

const EmailActions = ({email, onSuccess, onFailure}: Props) => {
    const [processModalOpen, setProcessModalOpen] = useState(false);
    const [messageApi, contextHolder] = useMessage();

    const [historyModalOpen, setHistoryModalOpen] = useState(false);

    return (
        <div>
            {contextHolder}
            <Space>
                <Tooltip title="处理回信">
                    <Button
                        type="link"
                        onClick={() => {
                            // setSelectedEmail(record);
                            setProcessModalOpen(true);
                        }}
                    >
                        <EditOutlined />
                    </Button>
                </Tooltip>
                <Tooltip title="查看操作历史">
                    <Button
                        type="link"
                        onClick={() => {
                            setHistoryModalOpen(true);
                        }}
                    >
                        <HistoryOutlined />
                    </Button>
                </Tooltip>

            </Space>


            <EmailProcessModal
                open={processModalOpen}
                email_id={email.id}
                onClose={() => setProcessModalOpen(false)}
                onSuccess={() => {
                        messageApi.success({content: "处理成功！"});
                        onSuccess?.();
                }}
                onFailure={
                    () => {
                        messageApi.error({content: "处理失败！"});
                        onFailure?.("处理失败！");
                    }
                }
            />

            <EmailActionHistoryModal
                open={historyModalOpen}
                emailId={email.id || undefined}
                onClose={() => setHistoryModalOpen(false)}
            />

        </div>
    )
}

export default EmailActions;