// 状态中文名称
export const STATUS_LABELS: Record<string, string> = {
    new: '新订单',
    waiting_label: '等待面单',
    label_created: '面单已生成',
    label_failed: '面单生成失败',
    synced: '已确认发货',
    sync_failed: '发货确认失败',
    uploaded: '已上传面单',
    upload_failed: '面单上传失败',
    completed: '处理完成',
    exception: '异常',
    cancelled: '已取消',
}

// 状态颜色（具体色号）
export  const STATUS_COLORS: Record<string, string> = {
    new: '#1677FF', // 蓝色
    waiting_label: '#69B1FF', // 浅蓝
    label_created: '#13C2C2', // 青绿
    label_failed: '#F5222D', // 红
    synced: '#7d6bde', // 紫色
    sync_failed: '#A8071A', // 深红
    uploaded: '#389E0D', // 稳定绿
    upload_failed: '#F5222D', // 红
    completed: '#52C41A', // 成功绿
    exception: '#FA8C16', // 橙色
    cancelled: '#BFBFBF', // 灰色
}

export const batchStatusColors: Record<string, string> = {
    pending: 'orange',
    processing: 'blue',
    completed: 'green',
    failed: 'red',
}

export const EMAIL_CATEGORY_COLORS: Record<string, string> = {
    invalid_email: "red",
    unsubscribe_request: "gold",
    keep_subscription: "green",
    email_change: "blue",
    other: "default",
}

export const EMAIL_CATEGORY_LABELS: Record<string, string> = {
    invalid_email: "邮箱失效",
    unsubscribe_request: "请求退订",
    keep_subscription: "保持订阅",
    email_change: "邮箱变更",
    other: "其他",
}