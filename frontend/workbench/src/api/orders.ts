import {get} from '@/utils/http'
import type {OrderStatus} from "@/api/enums.ts";

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
    tracking_number?: string
    tracking_url?: string
    carrier_code?: string
    batch_id?: string
}

export interface OrderQuery {
    status?: string
    channel_code?: string
    account_id?: string
    order_id?: string
    batch_id?: string
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


export interface OrderItemResponse {
    id: number
    item_number?: string
    order_id?: number
    name?: string
    sku?: string
    quantity?: number
    unit_price_excl_tax?: number
    subtotal_excl_tax?: number
    total_incl_tax?: number
    tax_rate_percent?: number
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
