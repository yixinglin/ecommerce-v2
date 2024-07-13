import { useState, useEffect } from "react";
import OrderList from "./OrderList";
import api from "../../axiosConfig";
import { getOrders } from "./restapi.js"
import "./OrderList.css";
import Pagination from "../common/Pagination.jsx";

const orderStatusClass = {
    "Shipped": "order-id order-status-shipped",
    "Unshipped": "order-id order-status-unshipped",
    "Delivered": "order-id order-status-delivered",
    "Canceled": "order-id order-status-canceled",      
    "Pending": "order-id order-status-canceled",
}

function AmazonOrderList() {
    document.title = "Amazon Orders";
    //  Fetch orders from API when component mounts
    const [orders, setOrders] = useState([]);
    const [daysago, setDaysAgo] = useState(7);
    const [apiKeyIndex, setApiKeyIndex] = useState(0);
    const [orderStatus, setOrderStatus] = useState("Unshipped");
    const [numOrders, setNumOrders] = useState(0);    
    const [offset, setOffset] = useState(0);
    const [limit, setLimit] = useState(20);
    const [batchPickSlipUrl, setBatchPickSlipUrl] = useState("#");
    const [batchPackSlipUrl, setBatchPackSlipUrl] = useState("#");
    const [batchParcelLabelUrl, setBatchParcelLabelUrl] = useState("#");
    const baseURL = api.defaults.baseURL;
    const pickpackURL = `${baseURL}/api/v1/pickpack/amazon`

    useEffect(() => {
        fetchOrders();
    }, [daysago, apiKeyIndex, orderStatus, offset, limit]);


    async function fetchOrders() {
        try {
            console.log("Fetching orders");
            const params = {};
            if (daysago) params.days_ago = daysago;
            if (orderStatus) params.status = orderStatus;
            if (apiKeyIndex) params.api_key_index = apiKeyIndex;
            if (offset) params.offset = offset;
            if (limit) params.limit = limit;
            console.log("Fetching orders with params", params);
            // const response = await api.get("/api/v1/amazon/orders", { params });            
            const response = await getOrders(params);
            const resp_orders = response.data.data.orders;
            const resp_size = response.data.data.size;
            setOrders(resp_orders);
            setNumOrders(resp_size);
            // Scroll to top of page on new fetch
            const orderIds = resp_orders.map(o => o.orderId);                        
            setBatchPickSlipUrl(`${pickpackURL}/batch-pick?refs=` + orderIds.join(";"))
            setBatchPackSlipUrl(`${pickpackURL}/batch-pack?refs=` + orderIds.join(";"))
            console.log("orderIds", orderIds);
            window.scrollTo(0, 0);
        } catch (error) {
            console.error("Error fetching orders from API", error);
        }
    }

    function handleDaysAgoChange(event) {
        setDaysAgo(event.target.value);
        setOffset(0);
    }

    function handleOrderStatusChange(event) {
        if (event.target.value === "" || event.target.value === "All" || event.target.value === null) {
            setOrderStatus(null);           
        } else {
            setOrderStatus(event.target.value);
        }
        setOffset(0);
    }

    function handleApiKeyIndexChange(event) {
        setApiKeyIndex(event.target.value);
        setOffset(0);
    }

    function handleClickPrevious(e) {
        console.log("Previous button clicked");
        const newOffset = offset - limit;
        if (newOffset >= 0) {
            setOffset(newOffset);
        } else {
        }
    }

    function handleClickNext(e) {
        console.log("Next button clicked");
        const newOffset = offset + limit;
        if (newOffset < numOrders) {
            setOffset(newOffset);
        } else {
            setOffset(offset);
        }
    }

    function handleLimitChange(event) {
        setLimit(parseInt(event.target.value));
        setOffset(0);
    }

    function getPaginationComponent() {
        return <div className="pagination panel">
                <select value={limit} onChange={ (e) => handleLimitChange(e) }>  
                        <option value="10">10 / Page</option>
                        <option value="20">20 / Page</option>
                        <option value="50">50 / Page</option>
                        <option value="100">100 / Page</option>
                        <option value="200">200 / Page</option>
                        <option value="500">500 / Page</option>
                        <option value="1000">1000 / Page</option>
                </select>                                  
                <span>{offset+1} - {Math.min(offset+limit, numOrders)} of {numOrders} </span>
                <button onClick={ (e) => handleClickPrevious(e) }>Previous</button>
                <button onClick={ (e) => handleClickNext(e)}>Next</button>
            </div> 
    }

    function handleOnPageChange(page) {
        setOffset((page-1)*limit);
    }

    return (
        <>  
        <h2 className="order-list-title"> Amazon Orders ({numOrders}) </h2>     
        {/* {getPaginationComponent()}   */}
        <div className="order-list-actions filters">
            <select value={daysago} onChange={ (e) => handleDaysAgoChange(e) }>  
                <option value="7">Last 7 days</option>                
                <option value="14">Last 14 days</option>
                <option value="30">Last 30 days</option>
                <option value="60">Last 60 days</option>
                <option value="90">Last 90 days</option>
                <option value="120">Last 120 days</option>
                <option value="180">Last 180 days</option>
            </select>
            <select value={orderStatus} onChange={ (e) => handleOrderStatusChange(e) }>  
                <option value="Unshipped">Unshipped</option>                
                <option value="Shipped">Shipped</option>
                <option value="Canceled">Canceled</option>
                <option value="">All</option>
            </select>
            <select value={apiKeyIndex} onChange={ (e) => handleApiKeyIndexChange(e) }>  
                <option value="0">API Key 0</option>                
            </select>          
        </div>                        
        <div className="order-list-actions download">
            <a href={batchPickSlipUrl} download><button>Pick-Slip</button></a>
            <a href={batchPackSlipUrl} download><button>Pack-Slip</button></a>            
            <a href="#" download><button disabled>Parcel-Labels</button></a>
        </div>
        {getPaginationComponent()}         
        <OrderList orders={orders} orderStatusClass={orderStatusClass} />  
        {getPaginationComponent()}                   
        <div  className="pagination"> 
            <Pagination currentPage={offset/limit+1} totalPages={Math.ceil(numOrders/limit)}
                onPageChange={handleOnPageChange} />
        </div>
        </>
    )
}

export default AmazonOrderList;