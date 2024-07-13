import React, { useState, useEffect } from "react";


function OrderList2(props) {
    const orders = props.orders;
    const orderStatusClass = {
        "Shipped": "order-id order-status-shipped",
        "Unshipped": "order-id order-status-unshipped",
        "Canceled": "order-id order-status-canceled",                
    }
    
    if (orders.length === 0) {
        return <div className="no-orders"> No orders found. </div>
    }

    const listItems = orders.map((order, index) => 
        <tr className="order-list-item">
            { renderOrderLines(order) }
        </tr>
        );

    function renderOrderLines(order) {
        const orderLines = order.items;
        const shipAddress = order.shipAddress;
        return orderLines.map((orderLine, index) =>             
            <>
                <td className="order-details" rowSpan={1}>                
                    <div className="cell-body">
                        {order.orderId}
                    </div>
                </td>   
                <td className="image" rowSpan={1}>
                    <div className="cell-body">
                        <img src={orderLine.image} alt={orderLine.name} />
                    </div>
                </td>
                <td className="product-name" rowSpan={1}>
                    <div className="cell-body">
                        <span>{orderLine.name}</span> <br/>
                        <span>SKU: {orderLine.sku}</span> <br/>
                        <span>Qty: {orderLine.quantity}</span> <br/>
                        <span>Transparency: {orderLine.additionalFields.isTransparency}</span> <br/>

                    </div>                    
                </td>  
                <td className="delivery-address" rowSpan={1}>
                    <div className="cell-body">
                        <span> <strong>Name 1</strong>: {shipAddress.name1} </span> <br/>
                        <span> <strong>Name 2</strong>: {shipAddress.name2} </span> <br/>
                        <span> <strong>Name 3</strong>: {shipAddress.name3} </span> <br/>
                        <span> <strong>Street</strong>: {shipAddress.street1} </span> <br/>
                        <span> <strong>City</strong>: {shipAddress.zipCode} {shipAddress.city} </span> <br/>
                        <span> <strong>State</strong>: {shipAddress.state} </span> <br/>
                        <span> <strong>Country</strong>: {shipAddress.country} </span> <br/>
                        <span> <strong>Mobile</strong>: {shipAddress.mobile} </span> <br/>
                        <span> <strong>Tel</strong>: {shipAddress.telephone} </span>   
                    </div>
                </td>
                <td className="tracking-id" rowSpan={1}>
                    <div className="cell-body">
                        <span>{order.trackingId}</span>
                    </div>
                </td>
            </>      
        );
    }


    return (
        // <div className="list-container">
        //     <ul className="order-list"> {listItems} </ul>
        // </div>
        <div className="list-container">
            <table className="order-list-table">
                <thead> 
                    <tr>    
                        <th><span>Order Details</span></th>
                        <th><span> Image</span> </th>
                        <th><span> Product Name</span> </th>
                        <th><span> Delivery Address</span> </th>
                        <th><span> Tracking ID</span> </th>
                        <th><span> Price</span> </th>
                    </tr>
                </thead>
            </table>
            <tbody>
                 {listItems}
            </tbody>
        </div>
    )
}

export default OrderList2;