import React from "react";
import { Carousel } from "antd";
import { SoundOutlined, SendOutlined, QuestionCircleOutlined } from "@ant-design/icons";

const Announcement = () => {
  return (
    <div style={{ 
      width: "100%", 
      background: "#f0f0f0", 
      padding: "8px 0", 
      textAlign: "center", 
      fontSize: "14px",
      fontWeight: "bold"
    }}>
      <Carousel autoplay  autoplaySpeed={4000} effect="scrollx" dots={false}>
        <div>
        <SoundOutlined /> <span> Sandbox-App für Testzwecke.</span>
        </div>
        <div>
        <QuestionCircleOutlined /> <span>Bei Fragen oder Vorschlägen kontaktieren Sie mich 
          </span>
        </div>
        <div>
        <SendOutlined /> <span> bitte unter <a href="mailto:yx.lin@hansagt.net"> yx.lin@hansagt.net</a>
          </span>
        </div>
      </Carousel>
    </div>
  );
};

export default Announcement;
