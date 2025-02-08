import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Table, Spin, Card, Button, Typography, message, Tooltip } from "antd";
import { fetch_stock_by_product_id, update_inventory_quantity, 
  fetch_putaway_rules, update_putaway_rule,
  quant_relocation_by_id } from "../rest/odoo"; // API 调用
import "./StockListView.css"; // 引入样式

const { Title } = Typography;

function StockListView() {
  const { product_id } = useParams();
  const [stockData, setStockData] = useState([]);
  const [putawayLocation, setPutawayLocation] = useState("None"); // 上架库位
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

    // 获取上架规则
    fetch_putaway_rules(product_id)
      .then((response) => {
        if (response.data.length > 0) {
          setPutawayLocation(response.data[0].location_out_name || "None");
        } else {
          setPutawayLocation("None");
        }
      })
      .catch(() => {
        setPutawayLocation("None");
      });
  }, [product_id]);

  const goBack = () => {
    navigate(-1);
  };

  // 处理上架库位更新
  const handleUpdatePutawayLocation = async () => {
    const newBarcode = prompt(`Enter the new putaway location barcode:`);
    if (!newBarcode) return;

    try {
      await update_putaway_rule(product_id, newBarcode);
      message.success(`Putaway location updated to ${newBarcode} successfully!`);
      setPutawayLocation(`Updated (${newBarcode})`);
    } catch (error) {
      message.error("Failed to update putaway location. Please try again.");
    }
  };

  // 处理库存更新
  const handleInventoryUpdate = async (record) => {
    const newQuantity = prompt(`Enter new inventory quantity for ${record.location_name}:`);
    if (!newQuantity) return;

    if (isNaN(newQuantity.trim())) {
      message.warning("Invalid input. Please enter a valid number.");
      return;
    }

    try {
      await update_inventory_quantity(record.id, parseInt(newQuantity, 10));
      message.success("Inventory updated successfully!");
      setStockData((prevData) =>
        prevData.map((item) =>
          item.id === record.id
            ? { ...item, inventory_quantity: parseInt(newQuantity, 10), inventory_quantity_set: true }
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
    if (!newBarcode) return;

    try {
      await quant_relocation_by_id(record.id, newBarcode);
      message.success(`Stock relocated to ${newBarcode} successfully!`);
      setStockData((prevData) =>
        prevData.map((item) =>
          item.id === record.id ? { ...item, location_code: newBarcode, location_name: `Updated (${newBarcode})` } : item
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
      width: 80,
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
      width: 80,
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
      width: 60,
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
      width: 80,
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
              scroll={{ x: 400 }}
            />
          </div>
        )}

        {/* 显示上架库位 */}
        <div className="putaway-location-container">
          <strong>Putaway Location: </strong>
          <span
            className="putaway-location"
            style={{ cursor: "pointer", color: "blue", textDecoration: "underline" }}
            onClick={handleUpdatePutawayLocation}
          >
            {putawayLocation}
          </span>
        </div>

        {/* <Button onClick={goBack} type="default" className="back-button">
          Back to Product
        </Button> */}
      </Card>
    </div>
  );
}

export default StockListView;
