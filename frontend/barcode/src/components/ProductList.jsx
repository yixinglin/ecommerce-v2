import React from "react";
import { Row, Col } from "antd";
import ProductCard from "./ProductCard";

const ProductList = ({ products }) => {
  return (
    <div style={{ padding: "20px" }}>
      <Row gutter={[16, 16]} justify="center">
        {products.map((product, index) => (
          <Col xs={24} sm={24} md={20} lg={16} xl={12} key={product.id}>
            <ProductCard product={product} index={index+1} />
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ProductList;
