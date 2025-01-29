import React from "react";
import { Row, Col } from "antd";
import ProductCard from "./ProductCard";

const ProductList = ({ products }) => {
  return (
    <div style={{ padding: "20px" }}>
      <Row gutter={[16, 16]}>
        {products.map((product) => (
          <Col xs={12} sm={12} md={8} lg={6} xl={4} key={product.id}>
            <ProductCard product={product} />
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ProductList;
