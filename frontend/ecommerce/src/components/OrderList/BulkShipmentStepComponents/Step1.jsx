import React, { useState, useEffect } from "react";
import api from "../../../axiosConfig";
import { getUnshippedOrders, parsePackSlip } from "../restapi.js"
import OrderList from "../OrderList.jsx";
import "../OrderList.css"

const orderStatusClass = {
    "Shipped": "order-id order-status-shipped",
    "Unshipped": "order-id order-status-unshipped",
    "Delivered": "order-id order-status-delivered",
    "Canceled": "order-id order-status-canceled",      
    "Pending": "order-id order-status-canceled",
}

function Step1({ nextStep, stepData }) {
    const baseURL = api.defaults.baseURL;
    const [orders, setOrders] = useState([]);
    const data = stepData;
    const sellerCenterURLs = {
        "bulk-confirm-shipment": "https://sellercentral.amazon.de/orders-v3/bulk-confirm-shipment",
        "packing-slip": "https://sellercentral.amazon.de/orders/packing-slip",
    }
    const [orderNumbers, setOrderNumbers] = useState([]);

    useEffect(() => {
        fetchUnshippedOrders();
    }, []); // Only run once on component mount

    async function fetchUnshippedOrders() {
        try {
            const params = {
                up_to_date: false,
                api_key_index: 0,
                country: "DE"
            }
            const response = await getUnshippedOrders(params);
            const respOrderNumbers = response.data.data.orderNumbers;
            console.log("Unshipped orders", respOrderNumbers);
            setOrderNumbers(respOrderNumbers);
        } catch (error) {
            console.log("Error fetching unshipped orders", error);
        }
    }

    async function handleParseButtonClick() {
        const textarea = document.getElementsByTagName("textarea")[0];
        // console.log(textarea.value);

        const data = {
            "country": "DE",
            "formatIn": "html",
            "formatOut": "object",
            "data": textarea.value
          }
        const response = await parsePackSlip(data);
        const respOrders = response.data.data.orders;
        console.log("Parsed orders", respOrders[0]);
        setOrders(respOrders);
        // Clear textarea
        textarea.value = "";
    }
    
    function handleNext() {
        const orderIds = orders.map(o => o.orderId);
        nextStep(orderIds);
    }

    return (
        <div>
            <h3>第一步：从亚马逊卖家中心复制装箱单。</h3> 
            <p> <strong> 请使用以下链接打开亚马逊卖家中心，并复制装箱单代码到下面的编辑框 </strong></p>
            <p><span> {`${sellerCenterURLs['packing-slip']}?orderIds=${orderNumbers.join(';')}`} </span></p>
            <textarea rows="10" cols="100"/>
            <br/>
            <button onClick={handleParseButtonClick}>Parse</button>
            <button onClick={handleNext}>Next</button>
            <div>
                { orders.length > 0 && <span> length: {orders.length} </span>}
            </div>
        </div>
    )
}

export default Step1;