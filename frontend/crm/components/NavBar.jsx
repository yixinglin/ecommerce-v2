import React from "react";
import { Menu } from "antd";
import { Link } from "react-router-dom";
import { SearchOutlined, UnorderedListOutlined } from "@ant-design/icons";

const NavBar = () => {
  return (
    <Menu mode="horizontal" theme="light" style={{ justifyContent: "center" }}>
      <Menu.Item key="discovery" icon={<SearchOutlined />}>
        <Link to="/map">KARTE</Link>        
      </Menu.Item>
      <Menu.Item key="list" icon={<UnorderedListOutlined />}>
        <Link to="/list">LISTE</Link>        
      </Menu.Item>
    </Menu>
  );
};

export default NavBar;
