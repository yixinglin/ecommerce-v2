import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { fetch_product_by_id, update_product_image, update_product_barcode, update_product_weight } from "../rest/odoo";
import { Card, Spin, Upload, message, Input } from "antd";
import { CameraOutlined, BarcodeOutlined, EditOutlined } from "@ant-design/icons";

function ProductView() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch_product_by_id(id).then((response) => {
      setProduct(response.data);
      setLoading(false);
    });
  }, [id]);

  // Handle image upload
  const handleImageUpload = async ({ file }) => {
    const formData = new FormData();
    formData.append("image", file);
    
    try {
      const response = await update_product_image(id, formData);
      message.success("Image uploaded successfully!");
      setProduct((prev) => ({ ...prev, image_url: response.data.image_url }));
    } catch (error) {
      message.error("Image upload failed. Please try again.");
    }
  };

  // Handle barcode update
  const handleBarcodeUpdate = async () => {
    const newBarcode = prompt("Enter the new barcode:");
    if (newBarcode) {
      try {
        const response = await update_product_barcode(id, newBarcode);
        message.success("Barcode updated successfully!");
        setProduct((prev) => ({ ...prev, barcode: response.data.barcode }));
      } catch (error) {
        message.error("Failed to update barcode. Please try again.");
      }
    }
  };

  // Handle weight update
  const handleWeightUpdate = async () => {
    const newWeight = prompt("Enter the new weight (kg):");
    if (newWeight) {
      try {
        const response = await update_product_weight(id, newWeight);
        message.success("Weight updated successfully!");
        setProduct((prev) => ({ ...prev, weight: response.data.weight }));
      } catch (error) {
        message.error("Failed to update weight. Please try again. " + error);
      }
    }
  };

  if (loading) {
    return <Spin style={{ display: "block", textAlign: "center", marginTop: "50px" }} />;
  }

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "top",
        alignItems: "center",
        backgroundColor: "#f9f9f9",
        padding: "16px",
      }}
    >
      <Card
        style={{
          width: "100%",
          maxWidth: "390px",
          borderRadius: "12px",
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
          background: "#fff",
          padding: "0px",
          overflow: "hidden",
        }}
        bodyStyle={{ padding: "0px" }}
      >
        {/* Image Upload */}
        <Upload
          customRequest={handleImageUpload}
          showUploadList={false}
        >
          <div
            style={{
              width: "100%",
              height: "auto",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "#fff",
              cursor: "pointer",
              position: "relative",
            }}
          >
            <img
              alt={product.name}
              src={product.image_url}
              style={{      
                width: "300px",
                height: "300px",
                objectFit: "contain", 
                display: "block" }}
            />
            <CameraOutlined
              style={{
                position: "absolute",
                bottom: "10px",
                right: "10px",
                fontSize: "24px",
                color: "#fff",
                background: "rgba(0, 0, 0, 0.5)",
                padding: "5px",
                borderRadius: "50%",
              }}
            />
          </div>
        </Upload>

        {/* Product Information */}
        <div style={{ padding: "16px", textAlign: "left" }}>
          <h2
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              color: "#333",
              marginBottom: "8px",
              wordBreak: "break-word",
              hyphens: "auto",
              lineHeight: "1.3",
            }}
          >
            {product.name}
          </h2>

          <p
            style={{ fontSize: "14px", color: "#666", marginBottom: "4px", cursor: "pointer" }}
            onClick={handleBarcodeUpdate}
          >
            <BarcodeOutlined style={{ marginRight: "6px", color: "#1890ff" }} />
            <strong>Barcode:</strong> {product.barcode || "N/A"}
          </p>

          <p
            style={{ fontSize: "14px", color: "#666", marginBottom: "4px", cursor: "pointer" }}
            onClick={handleWeightUpdate}
          >
            <EditOutlined style={{ marginRight: "6px", color: "#1890ff" }} />
            <strong>Weight:</strong> {product.weight} kg
          </p>

          <p
            style={{
              fontSize: "14px",
              fontWeight: "bold",
              color: product.qty_available > 0 ? "#28a745" : "#dc3545",
              marginBottom: "10px",
            }}
          >
            <strong>Stock:</strong> {product.qty_available} {product.uom}
          </p>

          {product.description && (
            <p
              style={{
                fontSize: "14px",
                color: "#666",
                marginTop: "10px",
                textAlign: "justify",
                lineHeight: "1.4",
              }}
            >
              <strong>Description:</strong> {product.description}
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}

export default ProductView;
