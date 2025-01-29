import React from "react";
import { Card } from "antd";

const ProductCard = ({ product }) => {
  return (
    <Card
      hoverable
      cover={<img alt={product.name} src={product.image_url} style={{ height: 120, objectFit: "contain" }} />}
    >
      <h3 style={{ fontSize: "10px", fontWeight: "bold", textAlign: "left" }}>{product.name.slice(0, 40)}</h3>
      {/* <p><strong>SKU:</strong></p> */}      
      <p style={{ fontSize: "9px", textAlign: "left" }}>{product.sku}</p>
      <p style={{ fontSize: "9px", textAlign: "left" }}>{product.barcode || "N/A"}</p>
    </Card>
  );
};

export default ProductCard;
