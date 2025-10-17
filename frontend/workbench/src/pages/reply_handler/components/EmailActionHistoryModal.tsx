
import React, { useEffect, useState } from "react";
import { Modal, Table, Tag, Typography, message } from "antd";
import { formatTime } from "@/utils/time";
import {type EmailActionResponse, listEmailActions} from "@/api/emails.ts";

const { Text } = Typography;

interface Props {
    open: boolean;
    emailId?: number;
    onClose: () => void;
}

const EmailActionHistoryModal: React.FC<Props> = ({ open, emailId, onClose }) => {
    const [loading, setLoading] = useState(false);
    const [records, setRecords] = useState<EmailActionResponse[]>([]);

    useEffect(() => {
        if (open && emailId) {
            loadActions();
        }
    }, [open, emailId]);

    const loadActions = async () => {
        try {
            setLoading(true);
            const data = await listEmailActions(emailId!);
            setRecords(data.data);
        } catch (err) {
            console.error(err);
            message.error("加载操作记录失败");
        } finally {
            setLoading(false);
        }
    };

    const columns = [
        {
            title: "时间",
            dataIndex: "created_at",
            width: 160,
            render: (v: string) => formatTime(v),
        },
        {
            title: "操作类型",
            dataIndex: "action_type",
            width: 150,
            render: (v: string) => {
                const labelMap: Record<string, string> = {
                    mark_invalid: "加入黑名单",
                    unsubscribe: "退订",
                    email_update: "邮箱变更",
                    no_action: "忽略",
                    other: "其他",
                };
                const colorMap: Record<string, string> = {
                    mark_invalid: "red",
                    unsubscribe: "gold",
                    email_update: "blue",
                    no_action: "default",
                    other: "gray",
                };
                return <Tag color={colorMap[v] || "default"}>{labelMap[v] || v}</Tag>;
            },
        },
        {
            title: "旧邮箱",
            dataIndex: "old_email",
            render: (text?: string) => text || "-",
        },
        {
            title: "新邮箱",
            dataIndex: "new_email",
            render: (text?: string) => text || "-",
        },
        {
            title: "备注",
            dataIndex: "note",
            ellipsis: true,
            render: (t: string) => t || "-",
        },
        {
            title: "操作人",
            dataIndex: "user",
            width: 120,
            render: (t: string) => <Text type="secondary">{t || "-"}</Text>,
        },
    ];

    return (
        <Modal
            title="📜 操作记录"
            open={open}
            onCancel={onClose}
            footer={null}
            width={850}
        >
            <Table
                rowKey="id"
                columns={columns}
                dataSource={records}
                loading={loading}
                pagination={false}
                bordered
                size="small"
            />
            {records.length === 0 && !loading && (
                <div style={{ textAlign: "center", marginTop: 16, color: "#999" }}>
                    暂无操作记录
                </div>
            )}
        </Modal>
    );
};

export default EmailActionHistoryModal;
