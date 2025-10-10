export  const  OrderStatus = {
    New: 'new',
    WaitingLabel: 'waiting_label',
    LabelCreated: 'label_created',
    LabelFailed: 'label_failed',
    Synced: 'synced',
    SyncFailed: 'sync_failed',
    Uploaded: 'uploaded',
    UploadFailed: 'upload_failed',
    Completed: 'completed',
    Exception: 'exception',
    Cancelled: 'cancelled',
} as const

export type OrderStatus = (typeof OrderStatus)[keyof typeof OrderStatus]

export const ChannelCode = {
    Amazon: 'amazon',
    WooCommerce: 'woocommerce',
    Kaufland: 'kaufland',
    Odoo: 'odoo',
    LingXing: 'lingxing',
    CustomERP: 'custom_erp',
} as const

export type ChannelCode = (typeof ChannelCode)[keyof typeof ChannelCode]

export const BatchStatus = {
    Pending: 'pending',
    Uploaded: 'uploaded',
    UploadFailed: 'upload_failed',
    Completed: 'completed',
}

export type BatchStatus = (typeof BatchStatus)[keyof typeof BatchStatus]