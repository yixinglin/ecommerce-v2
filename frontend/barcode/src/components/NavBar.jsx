import React from "react";
import { Menu } from "antd";
import { Link } from "react-router-dom";
import { AppstoreOutlined, TruckOutlined } from "@ant-design/icons";

const NavBar = () => {
  return (
    <Menu mode="horizontal" theme="light" style={{ justifyContent: "center" }}>
      <Menu.Item key="products" icon={<AppstoreOutlined />}>
        <Link to="/products">Products</Link>
      </Menu.Item>
      <Menu.Item key="delivery" icon={<TruckOutlined />}>
        <Link to="/delivery-order">Shipment</Link>
      </Menu.Item>
    </Menu>
  );
};

export default NavBar;
