import { List } from "antd";
import ProductCard from "./ProductCard";

const ProductList = ({ products }) => {
  return (
    <div style={{ padding: "20px" }}>
      <List
        grid={{
          gutter: 16,
          xs: 1,
          sm: 1,
          md: 2,
          lg: 3,
          xl: 4,
          xxl: 4
        }}
        dataSource={products}
        renderItem={(product, index) => (
          <List.Item key={product.id}>
            <ProductCard product={product} index={index + 1} />
          </List.Item>
        )}
      />
    </div>
  );
};

export default ProductList;
