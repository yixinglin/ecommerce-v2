import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Table, Spin, Card, Button, Typography, message, Tooltip } from "antd";
import { fetch_stock_by_product_id, update_inventory_quantity, quant_relocation_by_id } from "../rest/odoo"; // API 调用
import "./StockListView.css"; // 引入样式
import { render } from "react-dom";

const { Title } = Typography;

function StockListView() {
  const { product_id } = useParams();
  const [stockData, setStockData] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch_stock_by_product_id(product_id)
      .then((response) => {
        setStockData(response.data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [product_id]);

  const goBack = () => {
    navigate(-1);
  };

  // 处理库存更新
  const handleInventoryUpdate = async (record) => {
    const newQuantity = prompt(`Enter new inventory quantity for ${record.location_name}:`);
    if (newQuantity === null) {
      return;
    }

    if (isNaN(newQuantity) || newQuantity.trim() === "") {
      message.warning("Invalid input. Please enter a valid number.");
      return;
    }

    const parsedQuantity = parseInt(newQuantity, 10);

    try {
      await update_inventory_quantity(record.id, parsedQuantity);
      message.success("Inventory updated successfully!");
      // 更新库存数据
      setStockData((prevData) =>
        prevData.map((item) =>
          item.id === record.id
            ? {
                ...item,
                inventory_quantity: parsedQuantity,
                inventory_quantity_set: true, 
              }
            : item
        )
      );
    } catch (error) {
      message.error("Failed to update inventory. Please try again.");
    }
  };

  // 处理库存 Relocation
  const handleRelocation = async (record) => {
    const newBarcode = prompt(`Enter barcode of a new location:`);
    if (!newBarcode) {
      return;
    }

    try {
      await quant_relocation_by_id(record.id, newBarcode);
      message.success(`Stock relocated to ${newBarcode} successfully!`);

      // 更新库位信息
      setStockData((prevData) =>
        prevData.map((item) =>
          item.id === record.id
            ? {
                ...item,
                location_code: newBarcode,
                location_name: `Updated (${newBarcode})`, // 这里可以进一步优化
              }
            : item
        )
      );
    } catch (error) {
      message.error("Failed to relocate stock. Please try again.");
    }
  };

  const columns = [
    {
      title: "Location",
      dataIndex: "location_name",
      key: "location_name",
      width: 50,
      render: (_, record) => (
        <Tooltip title={record.product_name}>
          {record.location_name}
        </Tooltip>
      ),
    },
    {
      title: "Barcode",
      dataIndex: "location_code",
      key: "location_code",
      width: 50,
      render: (barcode, record) => (
        <span
          className="location-barcode"
          style={{ cursor: "pointer", color: "blue", textDecoration: "underline" }}
          onClick={() => handleRelocation(record)}
        >
          {barcode}
        </span>
      ),
    },
    {
      title: "Qty",
      dataIndex: "quantity",
      key: "quantity",
      width: 40,
      render: (quantity, record) => (
        <span className={quantity > 0 ? "stock-available" : "stock-out"}>
          {quantity} {record.product_uom}
        </span>
      ),
    },
    {
      title: "InvQty",
      dataIndex: "inventory_quantity",
      key: "inventory_quantity",
      width: 60,
      render: (_, record) => (
        <span
          className={record.inventory_quantity - record.quantity >= 0 || !record.inventory_quantity_set ? "stock-diff-positive" : "stock-diff-negative"}
          style={{ cursor: "pointer" }}
          onClick={() => handleInventoryUpdate(record)}
        >
          {record.inventory_quantity_set ? (
            <>
              {record.inventory_quantity}
              <span> {record.inventory_quantity - record.quantity > 0 ? "(盈)" : "(亏)"} </span>
            </>
          ) : (
            "-"
          )}
        </span>
      ),
    },
    {
      title: "Last Count Days",
      dataIndex: "last_count_days",
      key: "last_count_days",
      width: 80,
    },
  ];

  return (
    <div className="stock-list-container">
      <Card className="stock-list-card">
        <Title level={3}>Storage Location</Title>

        {loading ? (
          <Spin className="loading-spinner" />
        ) : (
          <div className="table-container">
            <Table
              dataSource={stockData}
              columns={columns}
              rowKey="id"
              pagination={{ pageSize: 20 }}
              size="small"
              scroll={{ x: 380 }}
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

export default StockListView;

