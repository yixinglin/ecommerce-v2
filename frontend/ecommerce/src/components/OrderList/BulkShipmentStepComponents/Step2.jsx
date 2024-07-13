import React, { useState } from "react";

function Step2({nextStep, stepData}) {

    // 这些ID是从Step1中获取的，表示成功得到解析的订单ID
    const orderIds = stepData; 

    console.log(orderIds);

    const handleNext = () => {
        // 逻辑来获取要发货的订单ID并显示链接到装箱单
        nextStep();
      };

    function handleGLSButtonClick() {
        console.log("Start button clicked");
        // 调用接口，生成快递单
    }

    return (
        <div>
            <h3>第二步：生成快递单.</h3>
            <p> 已经有{orderIds.length}个订单从第一步解析成功.</p>
            <button onClick={handleGLSButtonClick}>GLS </button>
            <button onClick={handleNext}>Next</button>
        </div>
    )
}

export default Step2;