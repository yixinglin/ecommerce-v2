// src/pages/EmailListPage.tsx
import React, {useEffect, useRef, useState} from "react";
import {Table, Button, Form, Select, Input, Space, message, Tag, Typography, Row, Col, Tooltip} from "antd";
import {ReloadOutlined, DownloadOutlined, SearchOutlined, CopyOutlined, ClearOutlined} from "@ant-design/icons";
import {useEmails} from "@/pages/reply_handler/hooks.ts";
import {EmailCategory, EmailStatus} from "@/api/enums.ts";
import {type EmailResponse, exportReport} from "@/api/emails.ts";
import PullEmailsModal from "@/pages/reply_handler/components/PullEmailsModal.tsx";
import {formatTime} from "@/utils/time.ts";
import EmailActions from "@/pages/reply_handler/components/EmailActions.tsx";
import {EMAIL_CATEGORY_COLORS, EMAIL_CATEGORY_LABELS} from "@/pages/order_fulfillment/components/enums.ts";


const {Option} = Select;
const {Title} = Typography;

const EmailListPage: React.FC = () => {
    const [form] = Form.useForm();
    const debounceTimer = useRef<number>(0)  // 防抖
    const [isResetting, setIsResetting] = useState(false)
    const [messageApi, contextHolder] = message.useMessage();
    const [pullEmailsModalOpen, setPullEmailsModalOpen] = useState(false);



    const {emails, loading, pagination, fetchEmails, resetEmails, refreshEmail} = useEmails({page: 1, limit: 10});

    // 初始化加载
    useEffect(() => {
        fetchEmails();
    }, []);

    // 提交搜索
    const handleSearch = async () => {
        const values = form.getFieldsValue();
        await fetchEmails(values, true);
    };

    const handleValuesChange = (_: any, allValues: any) => {
        if (isResetting) return; // 重置期间不触发防抖请求
        clearTimeout(debounceTimer.current)
        debounceTimer.current = setTimeout(() => {
            fetchEmails(allValues, true)
        }, 500);
    }

    // 重置表单
    const handleReset = async () => {
        setIsResetting(true)
        clearTimeout(debounceTimer.current)
        form.resetFields();
        await resetEmails();
        setTimeout(() => setIsResetting(false), 500);
    };


    const handleExport = async () => {
        const key = "exporting";
        messageApi.loading({ content: "正在导出报表...", key, duration: 0 });
        try {
            await exportReport();
            messageApi.success({ content: "导出成功", key });
        } catch (error) {
            console.error(error);
            messageApi.error({ content: "导出失败，请稍后再试", key });
        }
    };

    const columns = [
        {
            title: "序号",
            dataIndex: "id",
            width: 80,
        },
        {
            title:"收件时间",
            dataIndex: "received_at",
            width: 180,
            render: (value: string, record: EmailResponse) => {
                return <div>
                    <div>{formatTime(value)} </div>
                    <div style={{marginTop: 4, color: '#aaa'}}>{record.recipient}</div>
                </div>
            },
        },
        {
            title: "发件人",
            dataIndex: "sender",
            width: 300,
            // ellipsis: true,
            render: (value: string, record: EmailResponse) => {
                return <span>
                        {value} &nbsp;
                        <a onClick={() => {
                            navigator.clipboard.writeText(value || '')
                            messageApi.success(`复制成功: ${value}`)
                        }}>
                            <CopyOutlined/>
                        </a> <br/>
                    <span style={{color: '#aaa'}}>{record?.sender_name}</span>
                </span>
            }
        },
        {
            title:"拉取时间",
            dataIndex: "created_at",
            width: 130,
            render: (value: string) => formatTime(value),
        },
        {
            title: "邮件主题",
            dataIndex: "subject",
            ellipsis: true,
        },
        {
            title: "AI建议",
            dataIndex: "ai_result_text",
            width: 200,
            render: (value: string) => {
                return <Tooltip title={value}>
                    <span> {value?.slice(0, 30)}</span>
                </Tooltip>
            }
        },
        {
            title: "分类",
            dataIndex: "category",
            width: 80,
            render: (val: EmailCategory | null) => {
                if (!val) return <Tag>未分类</Tag>;
                return (
                    <Tag color={EMAIL_CATEGORY_COLORS[val] || "default"}>
                        {EMAIL_CATEGORY_LABELS[val] || val}
                    </Tag>
                );
            },
        },
        {
            title: "状态",
            dataIndex: "status",
            width: 70,
            render: (val: EmailStatus) => {
                if (val === EmailStatus.Processed) {
                    return <Tag color="blue">已处理</Tag>;
                } else {
                    return <Tag color="orange">未处理</Tag>;
                }
            }
        },
        {
            title: "操作",
            key: "action",
            width: 120,
            render: (record: EmailResponse) => (
                <EmailActions
                    email={record}
                    onSuccess={() => refreshEmail(record.id)}
                    onFailure={() => refreshEmail(record.id)}
                />
            ),
        },
    ];

    return (
        <div style={{padding: 24}}>
            {contextHolder}
            <Row justify="space-between" align="middle" style={{marginBottom: 16}}>
                <Col>
                    <Title level={4}>📬 邮件处理系统</Title>
                </Col>
                <Col>
                    <Space>
                        <Button
                            icon={<ReloadOutlined/>}
                            onClick={() => setPullEmailsModalOpen(true)}
                            type="primary"
                        >
                            同步新邮件
                        </Button>
                        <Button
                            icon={<DownloadOutlined/>}
                            onClick={handleExport}
                            type="default"
                        >
                            导出为 Excel
                        </Button>
                    </Space>
                </Col>
            </Row>

            <Form
                form={form}
                layout="inline"
                onFinish={handleSearch}
                onValuesChange={handleValuesChange}
                style={{marginBottom: 16}}
            >
                <Form.Item label="状态" name="status">
                    <Select
                        allowClear
                        placeholder="全部状态"
                        style={{width: 140}}
                    >
                        <Option value={EmailStatus.Unprocessed}>未处理</Option>
                        <Option value={EmailStatus.Processed}>已处理</Option>
                    </Select>
                </Form.Item>

                <Form.Item label="分类" name="category">
                    <Select
                        allowClear
                        placeholder="全部分类"
                        style={{width: 180}}
                    >
                        <Option value={EmailCategory.InvalidEmail}>邮箱失效</Option>
                        <Option value={EmailCategory.UnsubscribeRequest}>请求退订</Option>
                        <Option value={EmailCategory.KeepSubscription}>保持订阅</Option>
                        <Option value={EmailCategory.EmailChange}>邮箱变更</Option>
                        <Option value={EmailCategory.Other}>其他</Option>
                    </Select>
                </Form.Item>

                <Form.Item name="keyword" label="关键词">
                    <Input
                        placeholder="搜索发件人或主题"
                        allowClear
                        style={{width: 240}}
                    />
                </Form.Item>

                <Form.Item>
                    <Space>
                        <Button
                            icon={<SearchOutlined/>}
                            type="primary"
                            htmlType="submit"
                        >
                            搜索
                        </Button>
                        <Button icon={<ClearOutlined/>} onClick={handleReset}>重置</Button>
                    </Space>
                </Form.Item>
            </Form>

            {/* 邮件表格 */}
            <Table
                bordered
                rowKey="id"
                columns={columns}
                dataSource={emails}
                loading={loading}
                pagination={pagination}
            />

            <PullEmailsModal
                open={pullEmailsModalOpen}
                onClose={() => setPullEmailsModalOpen(false)}
                onSuccess={(count) => {
                    messageApi.success(`同步完成，新增 ${count} 封邮件`);
                    resetEmails(); // 调用 hook 刷新列表
                }}
            />


        </div>
    );
};

export default EmailListPage;
