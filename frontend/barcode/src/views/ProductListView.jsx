import React, { useState, useEffect, useRef } from "react";
import { Input, Spin, Button } from "antd";
import { fetch_all_products_brief } from "../rest/odoo.js";
import ProductList from "../components/ProductList.jsx";

function ProductListView() {
  const [productList, setProductList] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);
  const inputRef = useRef(null); // 用于控制输入框的引用

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

  const handleScroll = () => {
    if (listRef.current) {
      sessionStorage.setItem("scrollPosition", listRef.current.scrollTop);
    }
  };

  const searchProducts = () => {
    if (searchTerm.length < 3) {
      setProductList([]);
      sessionStorage.removeItem("productList");
      sessionStorage.removeItem("searchTerm");
      sessionStorage.removeItem("scrollPosition");
      return;
    }
    setLoading(true);

    fetch_all_products_brief(searchTerm).then((response) => {
      let products = response.data;
      products = products.filter((product) => product.active);

      setProductList(products);
      setLoading(false);

      sessionStorage.setItem("searchTerm", searchTerm);
      sessionStorage.setItem("productList", JSON.stringify(products));
      sessionStorage.setItem("scrollPosition", "0");

      // **收起键盘**
      if (inputRef.current) {
        inputRef.current.blur();
      }
    });
  };

  const handleInputChange = (e) => {
    setSearchTerm(e.target.value.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      searchProducts();
      e.target.blur(); // 失去焦点，收起键盘
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
          placeholder="Search for products..."
          value={searchTerm}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          allowClear
          style={{ flex: 1 }}
        />
        <Button onClick={searchProducts} type="primary">
          Search
        </Button>
        <Button onClick={clearSearch} type="default">
          Clear
        </Button>
      </div>

      {/* 产品列表部分，监听滚动事件 */}
      <div
        ref={listRef}
        onScroll={handleScroll}
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
