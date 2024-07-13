import { useState, useEffect } from "react";

function ParcelLabelView({ shipment }) {
    const b64Pdf = shipment.label;
    console.log("ParcelLabelView");
    return (
        <div>
            <h1>Parcel Label</h1>
            <iframe src={`data:application/pdf;base64,${b64Pdf}`} width="80%" height="700px" ></iframe>
        </div>
    );
}

export default ParcelLabelView;