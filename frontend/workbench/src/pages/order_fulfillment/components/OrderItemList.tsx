import { Card } from 'antd'
import {type OrderItemResponse} from '@/api/orders.ts'
import './OrderItemList.css'
import {useOrderItems} from "@/hooks/Order.ts";

export default function OrderItemList({ orderId }: { orderId: number }) {
    const { items, loading } = useOrderItems(orderId)
    if (loading) return <div>加载中...</div>
    return (
        <div className="wrapper">
            {(items || []).map((item: OrderItemResponse) => (
                <Card key={item.id} className="card" hoverable>
                    <div className="content">
                        {item.image_url && (
                            <img src={item.image_url} alt={item.name} className="image" />
                        )}
                        <div className="info">
                            <div className="name">{item.name}</div>
                            <div>SKU: {item.sku}</div>
                            <div>数量: {item.quantity}</div>
                            <div>单价: €{item.unit_price_excl_tax}</div>
                            <div>总价: €{item.total_incl_tax}</div>
                        </div>
                    </div>
                </Card>
            ))}
        </div>
    )
}
