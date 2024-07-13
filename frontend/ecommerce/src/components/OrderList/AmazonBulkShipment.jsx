import React, { useEffect, useState } from'react';
import Step1 from './BulkShipmentStepComponents/Step1.jsx';
import Step2 from './BulkShipmentStepComponents/Step2.jsx';
import Step3 from './BulkShipmentStepComponents/Step3.jsx';
import Step4 from './BulkShipmentStepComponents/Step4.jsx';
// Step 1: Get ids of orders to be shipped, show the link to the packing slip.
// Step 2: Parse packing slip and get the returned order ids
// Step 3: Show the list of orders with the shipping addresses
// Step 4: Start the bulk shipment process for the selected orders with one click
// Step 5: Get the id of the orders to be shipped
// Step 6: Display the parcel labels and print them out
// Step 7: Show the links to bulk confirm the shipment

function AmazonBulkShipment() {
    document.title = "Amazon Orders";
    const [currentStep, setCurrentStep] = useState(1);
    const [stepData, setStepData] = useState({});

    const nextStep = (data) => {
        setStepData(data);
        setCurrentStep(prev => prev + 1);
    };

   
    return (
        <div>
            {currentStep === 1 && <Step1 nextStep={nextStep} stepData={stepData} />}
            {currentStep === 2 && <Step2 nextStep={nextStep} stepData={stepData} />}
            {currentStep === 3 && <Step3 nextStep={nextStep} stepData={stepData} />}
            {currentStep === 4 && <Step4 nextStep={nextStep} stepData={stepData} />} 
        </div>
    )
}

export default AmazonBulkShipment;


{/* <h2>Step to Step Bulk-Shipment</h2>
<h3>Step 1: Download the packing slip from Amazon</h3> 
<p> <strong> 1.1 Please download the packing slip from Amazon Seller Central with the following link. </strong></p>
<p><span> {`${sellerCenterURLs['packing-slip']}?orderIds=${orderNumbers.join(';')}`} </span></p>
<br /> <br />

<p> <strong>Please confirm the shipped orders. Don't forget to do it. It's very important!!  </strong> </p>
<span> {`${sellerCenterURLs['bulk-confirm-shipment']}/${orderNumbers.join(';')}`} </span> */}