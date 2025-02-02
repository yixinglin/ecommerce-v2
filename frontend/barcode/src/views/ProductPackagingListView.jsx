import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Table, Spin, Card, Button, Typography, message, Tooltip } from "antd";
import { fetch_packaging_by_product_id, update_packaging_barcode } from "../rest/odoo"; // API 调用
import "./ProductPackagingListView.css"; // 样式文件
import { render } from "react-dom";

const { Title } = Typography;

function ProductPackagingListView() {
  const { product_id } = useParams();
  const [packagingData, setPackagingData] = useState([]);  
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch_packaging_by_product_id(product_id)
      .then((response) => {
        setPackagingData(response.data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [product_id]);

  const goBack = () => {
    navigate(-1);
  };

  // 处理条形码更新
  const handleBarcodeUpdate = async (record) => {
    const newBarcode = prompt(`Enter new barcode for ${record.name}:`);

    if (newBarcode === null) {
        return;
    }

    if (newBarcode.trim() === "") {
      message.warning("Invalid input. Please enter a valid barcode.");
      return;
    }

    try {
      await update_packaging_barcode(record.id, newBarcode);
      message.success("Barcode updated successfully!");

      // 更新前端数据
      setPackagingData((prevData) =>
        prevData.map((item) =>
          item.id === record.id
            ? { ...item, barcode: newBarcode }
            : item
        )
      );
    } catch (error) {
      message.error("Failed to update barcode. Please try again.");
    }
  };

  const columns = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
      width: 15,
    },
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      width: 60,
      render: (_, record) => (
        <Tooltip title={record.product_name} placement="topLeft">  
            <span>{record.name}</span>
        </Tooltip>
      ),

    },
    {
      title: "Barcode",
      dataIndex: "barcode",
      key: "barcode",
      width: 120,
      render: (barcode, record) => (
        <span
          style={{ cursor: "pointer", color: barcode ? "#1890ff" : "#d9d9d9" }}
          onClick={() => handleBarcodeUpdate(record)}
        >
          {barcode || "Click to set"}
        </span>
      ),
    },
    {
      title: "Qty",
      dataIndex: "qty",
      key: "qty",
      width: 50,
      render: (_, record) => (
        <span>{record.qty} {record.uom}</span>
      ),
    },
  ];

  return (
    <div className="packaging-list-container">
      <Card className="packaging-list-card">
        <Title level={3}>Packaging</Title>

        {loading ? (
          <Spin className="loading-spinner" />
        ) : (
          <div className="table-container">
            <Table
              dataSource={packagingData}
              columns={columns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
            //   scroll={{ x: 380 }}
            />
          </div>
        )}

        <Button onClick={goBack} type="default" className="back-button">
          Back to Product
        </Button>
      </Card>
    </div>
  );
}

export default ProductPackagingListView;
