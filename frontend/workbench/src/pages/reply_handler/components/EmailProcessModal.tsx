// src/pages/reply_handler/components/EmailProcessModal.tsx

import React, {useEffect, useState} from "react";
import {Modal, Descriptions, Typography, Divider, Radio, Form, Input, Space, Button,} from "antd";

import { EmailCategory} from "@/api/enums";
import {analyzeEmail, type EmailResponse, getEmail, processEmail} from "@/api/emails.ts";
import {formatTime} from "@/utils/time.ts";
import {
    RobotOutlined,
    MailOutlined,
    StopOutlined,
    InboxOutlined,
    CloseCircleOutlined,
    MessageOutlined
} from "@ant-design/icons";

const {Paragraph} = Typography;

interface EmailProcessModalProps {
    open: boolean;
    email_id: number;
    onClose: () => void;
    onSuccess?: (res: any) => void;
    onFailure?: () => void;
}

const EmailProcessModal: React.FC<EmailProcessModalProps> = ({
                                                                 open,
                                                                 email_id,
                                                                 onClose,
                                                                 onSuccess,
                                                                 onFailure,
                                                             }) => {
    const [form] = Form.useForm();
    const [submitting, setSubmitting] = React.useState(false);
    const [email, setEmail] = React.useState<EmailResponse>();
    const [analysisLoading, setAnalysisLoading] = useState(false);

    const fetchEmail = async () => {
        const res = await getEmail(email_id);
        setEmail(res);
    };

    useEffect(() => {
        if (open) {
            fetchEmail();
        }
    }, [open, email_id]);

    const handleAiAnalysis = async () => {
        try {
            setAnalysisLoading(true);
            if (email_id) {
                const res = await analyzeEmail(email_id);
                console.log(res);
                setEmail({...email!, ai_result_text: res.ai_result_text});
                onSuccess?.(res);
            }
        } catch (error) {
            console.log(error);
            onFailure?.();
        } finally {
            setAnalysisLoading(false);
        }
    }

    const handleSubmit = async () => {
        try {
            const values = await form.validateFields();
            setSubmitting(true);

            const payload = {
                action_type: values.action_type,
                category: values.category,
                note: values.note,
                old_email: values.old_email,
                new_email: values.new_email,
                user: "admin", // 可从登录信息中读取
            };
            const res = await processEmail(email!.id, payload);
            setSubmitting(false);
            onClose();
            onSuccess?.(res);
        } catch (err: any) {
            console.error(err);
            setSubmitting(false);
            onFailure?.();
        }
    };

    const categorySection = Form.useWatch("category", form);

    return (
        <Modal
            open={open}
            title="📬 邮件处理"
            onCancel={onClose}
            onOk={handleSubmit}
            okText="确认处理"
            cancelText="取消"
            confirmLoading={submitting}
            width={800}
            destroyOnClose
            bodyStyle={{maxHeight: '70vh', overflowY: 'auto'}}
        >
            {email ? (
                <>
                    {/* 邮件信息 */}
                    <Descriptions bordered size="small" column={1}>
                        <Descriptions.Item label="发件人">
                            {email.sender}
                        </Descriptions.Item>
                        <Descriptions.Item label="收件人">
                            {email.recipient}
                        </Descriptions.Item>
                        <Descriptions.Item label="收件时间">
                            {email.received_at && formatTime(email.received_at)}
                        </Descriptions.Item>
                        <Descriptions.Item label="主题">{email.subject}</Descriptions.Item>
                    </Descriptions>

                    <Divider/>

                    {/* 邮件原文 */}
                    <Typography.Title level={5}>📄 邮件原文（德语）</Typography.Title>
                    <Paragraph
                        style={{
                            background: "#fafafa",
                            padding: 12,
                            borderRadius: 8,
                            whiteSpace: "pre-wrap",
                        }}
                    >
                        {email.body || "（无正文）"}
                    </Paragraph>

                    <Divider/>

                    {/* AI 分析结果 */}
                    <Typography.Title level={5}>🤖 AI分析结果</Typography.Title>
                    <Paragraph
                        style={{
                            background: "#f6ffed",
                            padding: 12,
                            border: "1px solid #b7eb8f",
                            borderRadius: 8,
                            whiteSpace: "pre-wrap",
                        }}
                    >
                        {email.ai_result_text || "暂无 AI 分析结果"}
                    </Paragraph>
                    <Button
                        type="dashed"
                        icon={<RobotOutlined/>}
                        loading={analysisLoading}
                        onClick={handleAiAnalysis}
                        style={{
                            background: 'linear-gradient(135deg, #7b2ff7 0%, #f107a3 100%)',
                            border: 'none',
                            color: 'white',
                        }}
                    >
                        {analysisLoading ? "AI分析中..." : "AI分析"}
                    </Button>

                    <Divider/>

                    <Typography.Title level={5}>请选择分类</Typography.Title>

                    <Form
                        form={form}
                        layout="vertical"
                        initialValues={{
                            old_email: email.sender,
                        }}
                    >

                        <Form.Item
                            label="分类"
                            name="category"
                            rules={[{required: true, message: "请选择分类"}]}
                        >
                            <Radio.Group>
                                <Space direction="vertical">
                                    <Radio value={EmailCategory.InvalidEmail}>
                                        <StopOutlined style={{color: '#fa541c', marginRight: 6}}/>
                                        无效邮箱
                                    </Radio>
                                    <Radio value={EmailCategory.KeepSubscription}>
                                        <InboxOutlined style={{color: '#52c41a', marginRight: 6}}/>
                                        保留订阅
                                    </Radio>
                                    <Radio value={EmailCategory.UnsubscribeRequest}>
                                        <CloseCircleOutlined style={{color: '#ff4d4f', marginRight: 6}}/>
                                        取消订阅
                                    </Radio>
                                    <Radio value={EmailCategory.EmailChange}>
                                        <MailOutlined style={{color: '#1677ff', marginRight: 6}}/>
                                        邮箱变更
                                    </Radio>
                                    <Radio value={EmailCategory.Other}>
                                        <MessageOutlined style={{color: '#722ed1', marginRight: 6}}/>
                                        其他
                                    </Radio>
                                </Space>
                            </Radio.Group>
                        </Form.Item>


                        {/* 当选择邮箱变更时显示 */}
                        {categorySection === EmailCategory.EmailChange && (
                            <>
                                <Form.Item
                                    label="旧邮箱"
                                    name="old_email"
                                    rules={[{required: true, message: "请输入旧邮箱"}]}
                                >
                                    <Input placeholder="请输入旧邮箱"/>
                                </Form.Item>
                                <Form.Item
                                    label="新邮箱"
                                    name="new_email"
                                    rules={[
                                        {required: true, message: "请输入新邮箱"},
                                        {type: "email", message: "请输入有效邮箱地址"},
                                    ]}
                                >
                                    <Input placeholder="请输入新邮箱"/>
                                </Form.Item>
                            </>
                        )}

                        <Form.Item name="note" label="备注">
                            <Input.TextArea
                                placeholder="补充说明（可选）"
                                autoSize={{minRows: 2, maxRows: 4}}
                            />
                        </Form.Item>
                    </Form>
                </>
            ) : (
                <div style={{textAlign: "center", padding: "24px 0"}}>
                    未选择邮件
                </div>
            )}
        </Modal>
    );
};

export default EmailProcessModal;
