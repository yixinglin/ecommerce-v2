import {useEffect} from 'react'
import {useRequest} from './useRequest'
import {listOrderItems, listStatusLogs, type OrderStatusLog} from '@/api/orders'
import type {OrderItemResponse} from '@/api/orders'
import { getOrderAddress, type OrderAddress, type AddressType } from '@/api/orders'


interface ListResponse<T> {
    data: T[]
    total: number
    page: number
    limit: number
}

export function useOrderItems(orderId: number) {
    const {
        data,
        loading,
        run: fetchOrderItems,
    } = useRequest<ListResponse<OrderItemResponse>, number | undefined>(
        (id) => {
            if (typeof id !== 'number') {
                return Promise.reject(new Error('Invalid order ID'))
            }
            return listOrderItems(id)
        },
        {manual: true}
    )

    useEffect(() => {
        if (orderId) fetchOrderItems(orderId)
    }, [orderId])

    return {
        items: data?.data ?? [],
        loading,
        refetch: fetchOrderItems,
    }
}

export function useOrderStatusLogs(orderId: number) {
    const {
        data,
        loading,
        run: fetchOrderStatusLogs,
    } = useRequest<ListResponse<OrderStatusLog>, number>(
        (id) => {
            if (typeof id !== 'number') {
                return Promise.reject(new Error('Invalid order ID'))
            }
            return listStatusLogs(id)
        },
        {manual: true}
    )

    useEffect(() => {
        if (orderId) fetchOrderStatusLogs(orderId)
    }, [orderId])

    return {
        logs: data?.data ?? [],
        loading,
        refetch: fetchOrderStatusLogs,
    }
}

export function useOrderAddress(orderId: number, addressType: AddressType) {
    const {
        data,
        loading,
        run: fetchOrderAddress,
    } = useRequest<OrderAddress, number | undefined>(
        (id) => {
            if (typeof id !== 'number') {
                return Promise.reject(new Error('Invalid order ID'))
            }
            return getOrderAddress(id, addressType)
        },
        {manual: true}
    )

    useEffect(() => {
        if (orderId) fetchOrderAddress(orderId)
    }, [orderId])

    return {
        address: data,
        loading,
        refetch: fetchOrderAddress,
    }
}