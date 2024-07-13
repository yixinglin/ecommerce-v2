import api from "../../axiosConfig";

export function getOrders(params) {
    return api.get("/api/v1/amazon/orders", { params });
}

export function getUnshippedOrders(params) {
    return api.get("/api/v1/amazon/orders/unshipped", { params });
}

export function parsePackSlip(data) {
    return api.post("/api/v1/amazon/orders/packslip/parse", data);
}