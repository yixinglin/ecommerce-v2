import React, { useState, useEffect, useRef } from "react";
import { Input, Spin, Button } from "antd";
import { fetch_all_products_brief } from "../rest/odoo.js";
import ProductList from "../components/ProductList.jsx";

function ProductListView() {
  const [productList, setProductList] = useState([]); // 产品列表
  const [searchTerm, setSearchTerm] = useState(""); // 搜索关键字
  const [loading, setLoading] = useState(false); // 加载状态
  const [barcodeBuffer, setBarcodeBuffer] = useState(""); // 记录扫码枪输入
  const listRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const savedSearchTerm = sessionStorage.getItem("searchTerm");
    const savedProductList = sessionStorage.getItem("productList");
    const savedScrollPosition = sessionStorage.getItem("scrollPosition");

    if (savedSearchTerm) {
      setSearchTerm(savedSearchTerm);
    }
    if (savedProductList) {
      setProductList(JSON.parse(savedProductList));
    }

    setTimeout(() => {
      if (listRef.current && savedScrollPosition) {
        listRef.current.scrollTop = parseInt(savedScrollPosition, 10);
      }
    }, 100);
  }, []);

  // 监听全局按键输入（扫码枪输入）
  useEffect(() => {
    const handleKeyPress = (event) => {
      // 如果是数字或字母，加入到 `barcodeBuffer`
      if (/^[a-zA-Z0-9]$/.test(event.key)) {
        setBarcodeBuffer((prev) => prev + event.key);
      }

      // 如果按下 "Enter"，执行搜索
      if (event.key === "Enter") {
        if (barcodeBuffer.length > 3) { // 确保条形码有效
          searchProducts(barcodeBuffer);
          setBarcodeBuffer(""); // 清空缓存
        }
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [barcodeBuffer]); // 监听 `barcodeBuffer`

  // 执行搜索
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

    fetch_all_products_brief(searchValue).then((response) => {
      let products = response.data;
      products = products.filter((product) => product.active);

      setProductList(products);
      setLoading(false);

      // 存储搜索状态
      sessionStorage.setItem("searchTerm", searchValue);
      sessionStorage.setItem("productList", JSON.stringify(products));
      sessionStorage.setItem("scrollPosition", "0");
    });
  };

  const handleInputChange = (e) => {
    setSearchTerm(e.target.value.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      searchProducts(searchTerm);
      e.target.blur();
    }
  };

  const clearSearch = () => {
    setSearchTerm("");
    setProductList([]);
    sessionStorage.removeItem("searchTerm");
    sessionStorage.removeItem("productList");
    sessionStorage.removeItem("scrollPosition");
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* 固定顶部的搜索框 */}
      <div
        style={{
          position: "sticky",
          top: 0,
          zIndex: 10,
          backgroundColor: "#fff",
          padding: "10px",
          boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <Input
          ref={inputRef}
          placeholder="Scan barcode or type manually..."
          value={searchTerm}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          allowClear
          style={{ flex: 1 }}
        />
        <Button onClick={() => searchProducts(searchTerm)} type="primary">
          Search
        </Button>
        <Button onClick={clearSearch} type="default">
          Clear
        </Button>
      </div>

      {/* 产品列表部分，监听滚动事件 */}
      <div
        ref={listRef}
        style={{
          flex: 1,
          overflowY: "auto",
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

export default ProductListView;
