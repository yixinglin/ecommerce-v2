// src/components/PullEmailsModal.tsx

import React, { useState } from "react";
import { Modal, InputNumber, Form } from "antd";
import {pullEmails, type PullEmailsPayload} from "@/api/emails.ts";


interface PullEmailsModalProps {
    open: boolean;
    onClose: () => void;
    onSuccess?: (count: number) => void; // 拉取成功后的回调（用于刷新列表）
    onFailure?: () => void; // 拉取失败后的回调（用于提示错误信息）
}

const PullEmailsModal: React.FC<PullEmailsModalProps> = ({
                                                             open,
                                                             onClose,
                                                             onSuccess,
                                                             onFailure,
                                                         }) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);

    const handleOk = async () => {
        try {
            const values = await form.getFieldsValue();
            setLoading(true);
            const res = await pullEmails(values as PullEmailsPayload);

            setLoading(false);
            form.resetFields();
            onClose();
            onSuccess?.(res.success_count);
        } catch (err: any) {
            console.error(err);
            setLoading(false);
            onFailure?.();
        }
    };

    return (
        <Modal
            title="📥 拉取新邮件"
            open={open}
            onOk={handleOk}
            confirmLoading={loading}
            onCancel={onClose}
            okText="开始拉取"
            cancelText="取消"
            destroyOnClose
        >
            <Form
                form={form}
                layout="vertical"
                initialValues={{ limit: 20 }}
            >
                <Form.Item
                    label="拉取邮件数量"
                    name="limit"
                    rules={[
                        { required: true, message: "请输入要拉取的邮件数量" },
                        { type: "number", min: 1, max: 200, message: "范围 1-200" },
                    ]}
                >
                    <InputNumber
                        min={1}
                        max={200}
                        style={{ width: "100%" }}
                        placeholder="请输入数量（默认20）"
                    />
                </Form.Item>
            </Form>
        </Modal>
    );
};

export default PullEmailsModal;
