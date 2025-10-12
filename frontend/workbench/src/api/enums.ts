// -------------Order Fulfillment Enums----------

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


// ----Reply Handler----------
export const EmailStatus = {
    Processed: 'processed',
    Unprocessed: 'unprocessed',
}
export type EmailStatus = (typeof EmailStatus)[keyof typeof EmailStatus]


export const EmailCategory = {
    InvalidEmail: 'invalid_email',
    UnsubscribeRequest: 'unsubscribe_request',
    KeepSubscription: 'keep_subscription',
    EmailChange: 'email_change',
    Other: 'other',
}
export type EmailCategory = (typeof EmailCategory)[keyof typeof EmailCategory]

export const EmailActionType = {
    MarkInvalid:'mark_invalid',
    Unsubscribe: 'unsubscribe',
    EmailUpdate: 'email_update',
    NoAction: 'no_action',
    Other: 'other',
}
export type EmailActionType = (typeof EmailActionType)[keyof typeof EmailActionType]


