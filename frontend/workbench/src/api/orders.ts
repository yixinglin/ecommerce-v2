import {get, post, put} from '@/utils/http'
import type {OrderStatus} from "@/api/enums.ts";


export interface EnumOption {
    value: string
    label: string
}

export interface EnumResponse {
    channel_codes: EnumOption[]
    order_status: EnumOption[]
    address_type: EnumOption[]
    carrier_code: EnumOption[]
    operation_type: EnumOption[]
    integration_type: EnumOption[]
    order_batch_status: EnumOption[]
}

export function fetchEnums() {
    return get<EnumResponse>('/api/v1/order_fulfillment/enums')
}


export interface OrderResponse {
    id: number
    order_number?: string
    channel?: string
    account_id?: string
    status: OrderStatus
    created_at: string
    updated_at: string
    buyer_name?: string
    buyer_address?: string
    country_code?: string
    customer_note?: string
    tracking_number?: string
    tracking_url?: string
    tracking_info?: string
    delivered?: string
    carrier_code?: string
    batch_id?: string
    parcel_weights?: string
}

export const getOrder = (orderId: number) => {
    return get<OrderResponse>(`/api/v1/order_fulfillment/orders/${orderId}`)
}

export interface OrderQuery {
    status?: string
    channel_code?: string
    keyword?: string
    delivered?: string
    page?: number
    limit?: number
}

export interface ListResponse<T> {
    total: number
    page: number
    limit: number
    data: T[]
}

export const listOrders = (params?: OrderQuery) => {
    return get<ListResponse<OrderResponse>>('/api/v1/order_fulfillment/orders', { params })
}

export interface OrderUpdatePayload {
    status?: string
    carrier_code?: string
    parcel_weights?: string
}

export function updateOrder(orderId: number, data: OrderUpdatePayload) {
    return put<OrderResponse>(`/api/v1/order_fulfillment/orders/${orderId}/update`, data)
}

export function cancelOrder(orderId: number) {
    const payload: OrderUpdatePayload = {
        status: 'cancelled',
    }
    return updateOrder(orderId, payload)
}


export interface OrderItemResponse {
    id: number
    item_number?: string
    order_id?: number
    name?: string
    sku?: string
    quantity: number
    unit_price_excl_tax?: number
    subtotal_excl_tax?: number
    total_incl_tax?: number
    tax_rate_percent?: number
    weight?: number
    width?: number
    height?: number
    length?: number
    image_url?: string
    created_at?: string
    updated_at?: string
}

export const listOrderItems = (orderId: number) => {
    return get<ListResponse<OrderItemResponse>>(`/api/v1/order_fulfillment/orders/${orderId}/items`)
}

export interface OrderStatusLog {
    id: number
    order_id: number
    channel: string
    from_status: string | null
    to_status: string
    remarks?: string
    created_at: string // 如果你加了 changed_at 字段
}

export function listStatusLogs(orderId: number) {
    return get<ListResponse<OrderStatusLog>>(`/api/v1/order_fulfillment/orders/${orderId}/status_logs`)
}


export type AddressType = 'shipping' | 'billing'

export interface OrderAddress {
    id: number
    company?: string
    name?: string
    state_or_province?: string
    city?: string
    postal_code?: string
    address1?: string
    address2?: string
    phone?: string
    mobile?: string
    email?: string
    country?: string
    country_code?: string
    thumbnails?: string
}

export function getOrderAddress(orderId: number, type: AddressType) {
    return get<OrderAddress>(`/api/v1/order_fulfillment/orders/${orderId}/address/${type}`)
}

export function updateOrderAddress(orderId: number, type: AddressType, data: Partial<OrderAddress>) {
    return put<OrderAddress>(`/api/v1/order_fulfillment/orders/${orderId}/address/${type}`, data)
}

export function generateLabel(
    orderId: number,
    externalLogisticId: string,
    moreLabels: boolean = false
) {
    return post<{ success: boolean }>(
        `/api/v1/order_fulfillment/orders/${orderId}/generate_label`,
        {
            external_logistic_id: externalLogisticId,
            more_labels: moreLabels
        }
    )
}

export interface ShippingTrackingResponse {
    order_id: number
    tracking_number?: string
    carrier_code?: string
    location?: string
    country_code?: string
    description?: string
    status_text?: string
    created_at?: string
    updated_at?: string
}


export function update_shipping_tracking_status(
    orderId: number,
    externalLogisticId: string,
) {
    return post<ShippingTrackingResponse>(
        `/api/v1/order_fulfillment/orders/${orderId}/tracking_status?external_logistic_id=${externalLogisticId}`,
        {})
}

export interface PullOrdersPayload {
    channel_code: string
    account_id: string
}

export function pullOrders(data: PullOrdersPayload) {
    return post<{ success_count: number }>('/api/v1/order_fulfillment/orders/pull', data)
}


export function syncTrackingInfo(orderId: number) {
    return post<{ success: boolean }>(`/api/v1/order_fulfillment/orders/${orderId}/sync_tracking`)
}

export interface CreateBatchPayload {
    channel_code: string
    account_id?: string
    operator?: string
}

export function createBatch(data: CreateBatchPayload) {
    return post<{ batch_id: string }>('/api/v1/order_fulfillment/batches/create', data)
}

export interface BatchResponse {
    id: number
    batch_id: string
    order_count: number
    download_count: number
    status: string
    operator?: string
}

export function listBatches(params: { page?: number; limit?: number }) {
    return get<ListResponse<BatchResponse>>('/api/v1/order_fulfillment/batches', {params})
}


export function completeBatch(batchId: string) {
    return post<{ success: boolean }>(`/api/v1/order_fulfillment/batches/${batchId}/complete`)
}

export async function downloadBatchZip(batchId: string): Promise<void> {
    const blob = await get<Blob>(`/api/v1/order_fulfillment/batches/${batchId}/download`, {
        responseType: 'blob',
    })

    const filename = `${batchId}.zip`
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
}

export async function downloadOrderZip(orderId: number): Promise<void> {
    const blob = await get<Blob>(`/api/v1/order_fulfillment/orders/${orderId}/zip`, {
        responseType: 'blob',
    })

    const filename = `documents_${orderId}.zip`
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
}

export async function downloadOrderLabel(orderId: number): Promise<void> {
    const blob = await get<Blob>(`/api/v1/order_fulfillment/orders/${orderId}/labels/pdf`, {
        responseType: 'blob',
    })
    const filename = `label_${orderId}.pdf`
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
}