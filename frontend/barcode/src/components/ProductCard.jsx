import React from "react";
import { Card } from "antd";
import { useNavigate } from "react-router-dom";

const ProductCard = ({ product }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/product/${product.id}`); // 点击跳转到详情页
  };

  return (
    <Card
      hoverable
      onClick={handleClick}
      style={{
        cursor: "pointer",
        maxWidth: "600px",
        margin: "auto",
        borderRadius: "10px",
        boxShadow: "0 4px 10px rgba(0, 0, 0, 0.1)",
        background: "#fff",
      }}
      bodyStyle={{
        display: "flex", // 确保内容水平排列
        alignItems: "center",
        padding: "16px",
      }}
    >
      {/* 图片部分 */}
      <div
        style={{
          flexShrink: 0,
          width: "120px",
          height: "120px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#f5f5f5",
          borderRadius: "8px",
          overflow: "hidden",
        }}
      >
        <img
          alt=""
          src={product.image_url}
          style={{ width: "100%", height: "100%", objectFit: "contain" }}
        />
      </div>

      {/* 右侧信息部分 - 让所有文本左对齐 */}
      <div style={{ marginLeft: "16px", flex: 1, textAlign: "left" }}>
        <h3
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            marginBottom: "4px",
            color: "#333",
          }}
        >
          {product.name.slice(0, 40)}
        </h3>
        <p style={{ fontSize: "12px", color: "#666", margin: "2px 0" }}>
          <strong>SKU:</strong> {product.sku}
        </p>
        <p style={{ fontSize: "9px", color: "#666", margin: "2px 0" }}>
          <strong>Barcode:</strong> {product.barcode || "N/A"}
        </p>
        <p
          style={{
            fontSize: "12px",
            fontWeight: "bold",
            color: product.qty_available > 0 ? "#28a745" : "#dc3545",
            margin: "4px 0",
          }}
        >
          <strong>Stock:</strong> {product.qty_available} {product.uom}
        </p>
      </div>
    </Card>
  );
};

export default ProductCard;
