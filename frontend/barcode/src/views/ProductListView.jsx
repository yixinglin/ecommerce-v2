import React, { useState, useEffect, useLayoutEffect, useRef } from "react";
import { Input, Spin, Button } from "antd";
import { fetch_all_products_brief } from "../rest/odoo.js";
import ProductList from "../components/ProductList.jsx";
import "./ProductListView.css";

function ProductListView() {
  const [productList, setProductList] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [barcodeBuffer, setBarcodeBuffer] = useState(""); 
  const listRef = useRef(null);
  const inputRef = useRef(null);

  // ✅ `useLayoutEffect` 确保 `scrollTop` 在 `DOM` 渲染后恢复
  useLayoutEffect(() => {
    const savedSearchTerm = sessionStorage.getItem("searchTerm");
    const savedProductList = sessionStorage.getItem("productList");
    const savedScrollPosition = sessionStorage.getItem("scrollPosition");

    if (savedSearchTerm) setSearchTerm(savedSearchTerm);
    if (savedProductList) setProductList(JSON.parse(savedProductList));

    setTimeout(() => {
      if (listRef.current && savedScrollPosition) {
        listRef.current.scrollTop = parseInt(savedScrollPosition, 10) || 0;
      }
    }, 50);
  }, []);

  // ✅ 监听 `滚动事件`，实时更新 `sessionStorage`
  const handleScroll = () => {
    if (listRef.current) {
      sessionStorage.setItem("scrollPosition", listRef.current.scrollTop);
    }
  };

  // ✅ 监听 `扫码枪输入`
  useEffect(() => {
    const handleKeyPress = (event) => {
      if (/^[a-zA-Z0-9]$/.test(event.key)) {
        setBarcodeBuffer((prev) => prev + event.key);
      }
      if (event.key === "Enter") {
        if (barcodeBuffer.length > 3) {
          searchProducts(barcodeBuffer);
          setBarcodeBuffer("");
        }
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [barcodeBuffer]);

  // ✅ 触发搜索
  const searchProducts = (searchValue) => {
    if (searchValue.length < 3) {
      setProductList([]);
      sessionStorage.removeItem("productList");
      sessionStorage.removeItem("searchTerm");
      sessionStorage.removeItem("scrollPosition");
      return;
    }

    setSearchTerm(searchValue);
    setLoading(true);

    fetch_all_products_brief({"kw": searchValue, "page": 0, "page_size": 100}).then((response) => {
      let products = response.data;
      products = products.filter((product) => product.active);

      setProductList(products);
      setLoading(false);

      sessionStorage.setItem("searchTerm", searchValue);
      sessionStorage.setItem("productList", JSON.stringify(products));
      sessionStorage.setItem("scrollPosition", "0");
    });
  };

  // ✅ 处理 `搜索框` 变化（不触发搜索）
  const handleInputChange = (e) => {
    setSearchTerm(e.target.value.trim());
  };

  // ✅ 监听 `回车键` 触发搜索，并隐藏键盘（适用于移动端）
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      searchProducts(searchTerm);
      e.target.blur(); // 让键盘收起
    }
  };

  // ✅ 清空搜索
  const clearSearch = () => {
    setSearchTerm("");
    setProductList([]);
    sessionStorage.removeItem("searchTerm");
    sessionStorage.removeItem("productList");
    sessionStorage.removeItem("scrollPosition");
  };

  return (
    <div className="product-list-container">
      {/* 固定顶部的搜索框 */}
      <div className="product-list-header">
        <Input
          ref={inputRef}
          placeholder="Scan barcode or type manually..."
          value={searchTerm}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          allowClear
          className="product-list-search"
        />
        <Button onClick={() => searchProducts(searchTerm)} type="primary">
          Search
        </Button>
        <Button onClick={clearSearch} type="default">
          Clear
        </Button>
      </div>

      {/* 产品列表部分，监听滚动事件 */}
      <div ref={listRef} className="product-list-content" onScroll={handleScroll}>
        {loading ? (
          <Spin className="loading-spinner" />
        ) : (
          <ProductList products={productList} />
        )}
      </div>
      <p style={{textAlign: "left", fontSize: "8px", color: "gray"}}>%orderline%</p>
    </div>    
  );
}

export default ProductListView;
