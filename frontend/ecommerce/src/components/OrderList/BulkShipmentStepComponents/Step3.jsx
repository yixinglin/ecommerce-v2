import React from 'react';

function Step3({ nextStep, stepData }) {
  const handleNext = () => {
    // 逻辑来显示订单列表及其送货地址
    nextStep();
  };

  return (
    <div>
      <h2>Step 3: Show order list with shipping addresses</h2>
      <button onClick={handleNext}>Next</button>
    </div>
  );
}

export default Step3;
