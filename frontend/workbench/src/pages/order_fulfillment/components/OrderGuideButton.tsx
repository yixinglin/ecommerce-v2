import { Modal, Button } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import { useState } from 'react'

export default function OrderGuideModalButton() {
    const [open, setOpen] = useState(false)

    return (
        <>
            <Button
                icon={<InfoCircleOutlined />}
                onClick={() => setOpen(true)}
                style={{ marginBottom: 16 }}
            >
                操作指引
            </Button>

            <Modal
                open={open}
                title="🎯 操作流程指引"
                onCancel={() => setOpen(false)}
                onOk={() => setOpen(false)}
                okText="知道了"
                cancelButtonProps={{ style: { display: 'none' } }}
            >
                <ol style={{ paddingLeft: 20, fontSize: 14, lineHeight: '24px' }}>
                    <li>
                        🛎️ <strong style={{ color: '#1677ff' }}>步骤 1：</strong>
                        点击右上角的 <span style={{ color: '#52c41a' }}><strong>“拉取订单”</strong></span> 按钮，<span style={{ color: '#8c8c8c' }}>从平台同步最新订单</span>。
                    </li>
                    <li>
                        🧾 <strong style={{ color: '#1677ff' }}>步骤 2：</strong>
                        在订单列表中，逐个点击
                        <span style={{ color: '#fa8c16', marginLeft: 4 }}><strong>“生成面单”</strong></span> 和
                        <span style={{ color: '#fa8c16', marginLeft: 4 }}><strong>“确认发货”</strong></span> 按钮，
                        <span style={{ color: '#8c8c8c' }}>完成每一笔订单处理</span>。
                    </li>
                    <li>
                        📦 <strong style={{ color: '#1677ff' }}>步骤 3：</strong>
                        点击 <span style={{ color: '#722ed1' }}><strong>“生成订单批次”</strong></span>，将多个订单打包为一个批次。
                    </li>
                    <li>
                        💾 <strong style={{ color: '#1677ff' }}>步骤 4：</strong>
                        跳转到 <span style={{ color: '#52c41a' }}><strong>“订单批次页面”</strong></span>，
                        点击 <strong style={{ color: '#1677ff' }}>“下载”</strong> 按钮，<span style={{ color: '#8c8c8c' }}>批量下载所有面单（ZIP 文件）</span>。
                    </li>
                    <li>
                        ✅ <strong style={{ color: '#1677ff' }}>步骤 5：</strong>
                        所有订单处理完成后，点击
                        <span style={{ color: '#ff4d4f', marginLeft: 4 }}><strong>“完成批次”</strong></span>，
                        <span style={{ color: '#8c8c8c' }}>标记该批次已完成</span>。
                    </li>
                </ol>
            </Modal>
        </>
    )
}
