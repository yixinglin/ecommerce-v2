import {useEffect, useState} from 'react'
import {useRequest} from '../../hooks/useRequest.ts'
import type {OrderItemResponse} from '@/api/orders.ts'
import {
    type AddressType,
    getOrder,
    getOrderAddress,
    listOrderItems,
    listOrders,
    listStatusLogs,
    type OrderAddress,
    type OrderQuery,
    type OrderResponse,
    type OrderStatusLog
} from '@/api/orders.ts'


interface ListResponse<T> {
    data: T[]
    total: number
    page: number
    limit: number
}

export function useOrders(initialParams: OrderQuery = {page: 1, limit: 10}) {
    const [orders, setOrders] = useState<OrderResponse[]>([])
    const [params, setParams] = useState<OrderQuery>(initialParams)

    const {
        data,
        loading,
        run: runList,
    } = useRequest<ListResponse<OrderResponse>, OrderQuery>(listOrders, {
        manual: true,
        defaultParams: initialParams,
        onSuccess: (res) => {
            if (res?.data) setOrders(res.data)
        },
    })

    /** 加载订单列表（可带筛选） */
    const fetchOrders = async (query?: Partial<OrderQuery>, resetPage = false) => {
        const merged = {...params, ...query}
        if (resetPage) merged.page = 1
        setParams(merged)
        await runList(merged)
    }

    /** 刷新单条订单 */
    const refreshOrder = async (id: number) => {
        const res = await getOrder(id)
        if (res) {
            setOrders((prev) => prev.map((o) => (o.id === id ? res : o)))
        }
    }

    /** 重置订单列表 */
    const resetOrders = async () => {
        setParams(initialParams)
        await runList(initialParams)
    }

    /** 分页配置 */
    const pagination = {
        current: data?.page || params.page || 1,
        pageSize: data?.limit || params.limit || 10,
        total: data?.total || 0,
        showTotal: (total: any) => `共 ${total} 条`,
        showSizeChanger: true,
        onChange: (page: number, limit: number) => {
            fetchOrders({page, limit})
        },
    }

    return {
        orders,
        loading,
        pagination,
        fetchOrders,
        refreshOrder,
        resetOrders,
    }
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
