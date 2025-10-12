import { Card, Row, Col } from 'antd'
import { type OrderItemResponse } from '@/api/orders.ts'
import './OrderItemList.css'
import { useOrderItems } from "@/pages/order_fulfillment/hooks.ts"

export default function OrderItemList({ orderId }: { orderId: number }) {
    const { items, loading } = useOrderItems(orderId)
    if (loading) return <div className="loading">加载中...</div>

    // 计算总重量
    const totalWeight = (items || []).reduce((sum, item) => {
        return sum + (item.weight || 0) * (item.quantity || 0)
    }, 0)


    return (
        <div className="order-items">
            {(items || []).map((item: OrderItemResponse) => (
                <Card key={item.id} className="order-card" hoverable>
                    <div className="card-inner">
                        <Row gutter={16} align="top" wrap={false}>
                            {/* 固定宽度，不收缩 */}
                            <Col flex="0 0 100px">
                                <div className="item-image-wrapper">
                                    {item.image_url && (
                                        <img src={item.image_url} alt={item.name} className="item-image" />
                                    )}
                                </div>
                            </Col>

                            {/* 右侧信息自适应 */}
                            <Col flex="auto" className="item-info-area">
                                <div className="item-header">
                                    <div className="item-name">{item.name}</div>
                                    <div className="item-sku">SKU: {item.sku}</div>
                                </div>

                                <Row gutter={12} className="item-details">
                                    <Col xs={24} sm={12}>
                                        <div>单价: €{item.unit_price_excl_tax}</div>
                                        <div>总价: €{item.total_incl_tax}</div>
                                    </Col>
                                    <Col xs={24} sm={12}>
                                        <div>重量: {item.weight} kg / 件</div>
                                        <div>尺寸: {item.width} × {item.height} × {item.length}</div>
                                        <div>总重: {item.quantity * (item.weight || 0)} kg</div>
                                    </Col>
                                </Row>
                            </Col>
                        </Row>

                        {/* 右下角数量徽标 */}
                        <div className="item-quantity">×{item.quantity}</div>
                    </div>
                </Card>
            ))}

            {items && items.length > 0 && (
                <div className="total-weight">
                    总重合计：<span className="weight-value">{totalWeight} kg</span>
                </div>
            )}
        </div>
    )
}
