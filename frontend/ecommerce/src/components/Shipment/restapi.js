import api from "../../axiosConfig";


export function downloadShipmentLabel(shipmentIds) {
    const params = {
        refs: shipmentIds.join(";"),
        labels: true,
    }
    return api.get("/api/v1/carriers/gls/shipments", { params });
}

export function postShipmentForm(data) {    
    const consignee = {
        "name1": data.name1,
        "name2": data.name2,
        "name3": data.name3,
        "street1": `${data.street1} ${data.houseNumber}`,
        "zipCode": data.zipCode,
        "city": data.city,
        "province": data.province,
        "country": data.country,  //TODO 
        "email": data.email,
        "telephone": data.telephone,
        "mobile": data.mobile,
    }
    const parcel = {
        "weight": data.weight,
        "comment": data.content,
        "content": data.content,
    }

    const numberOfPackages = data.numberOfPackages;
    const parcels = [];
    //  Copy the parcel object and add it to the packages array
    for (let i = 0; i < numberOfPackages; i++) {
        parcels.push(Object.assign({}, parcel));
    }
    const references = [data.references];
    const carrier = data.carrierName.toLowerCase();
    const shipment = {        
        "consignee": consignee,
        "parcels": parcels,
        "references": references,
        "carrier": carrier,
    }
    console.log("Posting shipment: ", shipment);
    return api.post("/api/v1/carriers/gls/shipments", shipment);
}