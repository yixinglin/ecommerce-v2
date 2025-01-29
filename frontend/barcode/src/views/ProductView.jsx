import React, { useState } from "react";
import { Input, Spin } from "antd";
import { fetch_all_products_brief } from "../rest/odoo";
import ProductList from "../components/ProductList.jsx";

function ProductView() {
  const [productList, setProductList] = useState([]); // 产品列表
  const [searchTerm, setSearchTerm] = useState(""); // 搜索关键字
  const [loading, setLoading] = useState(false); // 加载状态

  // 搜索产品
  const searchProducts = (keyword) => {
    if (keyword.length < 3) {
      setProductList([]); // 输入小于3个字符时清空产品列表
      return;
    }
    setLoading(true); // 设置加载中状态
    fetch_all_products_brief(keyword).then((response) => {
      let products = response.data.slice(0, 30); // 最多显示前30个结果
      products = products.filter((product) => product.active); // 仅显示 active 状态的产品
      setProductList(products);
      setLoading(false); // 关闭加载状态
    });
  };

  // 处理搜索框输入变化
  const handleSearch = (e) => {
    const keyword = e.target.value.trim();
    setSearchTerm(keyword);
    if (keyword.length >= 3) {
      searchProducts(keyword); // 调用搜索函数
    } else {
      setProductList([]); // 清空列表
    }
  };

  return (
    <div style={{ height: "100vh", width: "90vw", display: "flex", flexDirection: "column" }}>
      {/* 固定顶部的搜索框 */}
      <div
        style={{
          position: "sticky",
          top: 0,          
          zIndex: 10,
          backgroundColor: "#fff",
          padding: "10px 10px",
          boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        }}
      >
        <h3>Products</h3>
        <Input
          placeholder="Search for products..."
          value={searchTerm}
          onChange={handleSearch}
          allowClear
          style={{ marginBottom: "10px", width: "100%" }}
        />
      </div>

      {/* 产品列表部分 */}
      <div
        style={{
          flex: 1,
          overflowY: "auto", // 允许列表部分滚动
          padding: "10px",
          backgroundColor: "#f9f9f9",
        }}
      >
        {loading ? (
          <Spin style={{ display: "block", textAlign: "center", marginTop: "20px" }} />
        ) : (
          <ProductList products={productList} />
        )}
      </div>
    </div>
  );
}

export default ProductView;
