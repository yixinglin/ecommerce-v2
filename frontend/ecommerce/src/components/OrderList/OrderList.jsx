import countryFlagEmoji from "country-flag-emoji";

function OrderList(props) {
    const orders = props.orders;
    const orderStatusClass = props.orderStatusClass;
    
    if (orders.length === 0) {
        return <div className="no-orders"> No orders found. </div>
    }

    const listItems = orders.map((order, index) => {
        const shipAddress = order.shipAddress;
        const elm = <li key={index} className="order-list-item">
                <p className={ orderStatusClass? orderStatusClass[order.status]: "" }> {order.orderId} </p>     
                <div className="order-container">
                    <div className="order-line-buyer">                                  
                        <div className="buyer-cell">
                            <span> <strong>Name 1</strong>: {shipAddress.name1} </span> <br/>
                            <span> <strong>Name 2</strong>: {shipAddress.name2} </span> <br/>
                            <span> <strong>Name 3</strong>: {shipAddress.name3} </span> 
                        </div>                          
                        <div className="buyer-cell">
                            <span> <strong>Street</strong>: {shipAddress.street1} </span> <br/>
                            <span> <strong>City</strong>: {shipAddress.zipCode} {shipAddress.city} </span> <br/>
                            <span> <strong>State</strong>: {shipAddress.province} </span> <br/>
                            <span> <strong>Country</strong>: {countryFlagEmoji.get("DE").emoji} {countryFlagEmoji.get("DE").name} ({shipAddress.country}) </span>
                        </div>
                        <div className="buyer-cell">
                            <span> <strong>Mobile</strong>: {shipAddress.mobile} </span> <br/>
                            <span> <strong>Tel</strong>: {shipAddress.telephone} </span> <br/>   
                            <span> <strong>Email</strong>: {shipAddress.email} </span> 
                        </div>                                                    
                    </div>
                    <ul> {renderOrderLines(order)} </ul>
                </div>             
            </li>
            return elm;
        }        
    );

    function renderOrderLines(order) {
        const orderLines = order.items;
        const shipAddress = order.shipAddress;
        return orderLines.map((orderLine, index) => 
            <li key={index} className="order-line">                
                <div className="order-line-container">
                    <div className="order-line-image">                    
                        <img src={orderLine.image} alt={orderLine.name}></img>
                    </div>
                    <div className="order-cell product-name">
                        <span> {orderLine.name} </span> <br/>
                        <br/>
                        <span> <strong>Purchased</strong>: {order.purchasedAt} </span><br/>       
                        <span> <strong>Status</strong>: {order.status} </span><br/>                                                          
                        <br/>                            
                        { orderLine.additionalFields.isTransparency? <><span className="isTransparency">Transparency</span><br/></> : null }
                    </div>
                    <div className="order-cell order-line-details">               
                        { orderLine.sku ? <><span> <strong>SKU</strong>: {orderLine.sku}<br/> </span></> : null }
                        { orderLine.asin ? <><span> <strong>ASIN</strong>: {orderLine.asin}<br/> </span></> : null }
                        { orderLine.ean? <><span> <strong>EAN</strong>: {orderLine.ean}<br/> </span></> : null }                        
                        <span> <strong>Qty</strong>: {orderLine.quantity} </span>  <br/>                         
                    </div>
                    <div className="order-cell order-line-price">
                        <span> <strong>Unit Price</strong>: {Math.floor(orderLine.unitPrice * 100) / 100} </span><br/>
                        <span> <strong>Subtotal</strong>: { Math.floor(orderLine.subtotal * 100) / 100 } </span><br/>
                        <span> <strong>Total Price</strong>: { Math.floor(orderLine.total * 100) / 100 } </span> <br/>
                        <br/>                                                                                             
                        <span> <strong>Track ID</strong>: {order.trackIds} </span>
                    </div>
                </div>
                {index < orderLines.length - 1 && <hr/>}                
            </li>
        );
    }


    return (
        <div className="list-container">
            <ul className="order-list"> {listItems} </ul>
        </div>
    )
}

export default OrderList;