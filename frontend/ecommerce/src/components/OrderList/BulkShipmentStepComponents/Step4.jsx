import React from 'react';

function Step4({ nextStep, stepData }) {
  const handleNext = () => {
    // 逻辑来开始批量发货流程
    nextStep();
  };

  return (
    <div>
      <h2>Step 4: Start bulk shipment process</h2>
      <button onClick={handleNext}>Next</button>
    </div>
  );
}

export default Step4;
