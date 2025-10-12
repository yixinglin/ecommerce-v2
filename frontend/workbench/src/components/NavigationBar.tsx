import {Menu} from "antd";
import {Link} from "react-router-dom";
import {AppstoreOutlined, TruckOutlined} from "@ant-design/icons";

const { SubMenu } = Menu;

const NavigationBar = () => {
    return (
        <Menu mode="horizontal" theme="light" style={{justifyContent: "center"}}>
            <Menu.Item key="homepage" icon={<AppstoreOutlined/>}>
                <Link to="/">主页</Link>
            </Menu.Item>
            <Menu.Item key="reply_handler" icon={<TruckOutlined/>}>
                <Link to="/reply_handler">退信处理</Link>
            </Menu.Item>
            <SubMenu key="submenu" title="更多" icon={<AppstoreOutlined/>}   >
                <Menu.Item key="orders" icon={<AppstoreOutlined/>}>
                    <Link to="/orders">订单处理</Link>
                </Menu.Item>
                <Menu.Item key="batches" icon={<AppstoreOutlined/>}>
                    <Link to="/batches">订单批次</Link>
                </Menu.Item>
            </SubMenu>
            <Menu.Item key="about" icon={<TruckOutlined/>}>
                <Link to="/about">About</Link>
            </Menu.Item>
        </Menu>
    );
}

export default NavigationBar;