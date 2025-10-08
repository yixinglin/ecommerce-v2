import {Menu} from "antd";
import {Link} from "react-router-dom";
import {AppstoreOutlined, TruckOutlined} from "@ant-design/icons";

const NavigationBar = () => {
    return (
        <Menu mode="horizontal" theme="light" style={{justifyContent: "center"}}>
            <Menu.Item key="homepage" icon={<AppstoreOutlined/>}>
                <Link to="/">Home</Link>
            </Menu.Item>
            <Menu.Item key="orders" icon={<AppstoreOutlined/>}>
                <Link to="/orders">Orders</Link>
            </Menu.Item>
            <Menu.Item key="about" icon={<TruckOutlined/>}>
                <Link to="/about">About</Link>
            </Menu.Item>
        </Menu>
    );
}

export default NavigationBar;