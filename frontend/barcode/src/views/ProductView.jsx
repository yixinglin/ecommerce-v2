import React, { useState, useEffect } from "react";
import { useParams, useNavigate  } from "react-router-dom";
import { fetch_product_by_id, update_product_image, 
      update_product_barcode, update_product_weight } from "../rest/odoo";
import { Card, Spin, Upload, message, Button } from "antd";
import { CameraOutlined, BarcodeOutlined, EditOutlined, NodeIndexOutlined } from "@ant-design/icons";
import "./ProductView.css"; // 引入 CSS 文件

function ProductView() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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
        message.error("Failed to update weight. Please try again.");
      }
    }
  };

  if (loading) {
    return <Spin style={{ display: "block", textAlign: "center", marginTop: "50px" }} />;
  }

  return (
    <div className="product-view-container">
      <Card className="product-card">
        {/* Image Upload */}
        <Upload customRequest={handleImageUpload} showUploadList={false}>
          <div className="product-image-container">
            <img alt={product.name} src={product.image_url} className="product-image" />
            <CameraOutlined className="camera-icon" />
          </div>
        </Upload>

        {/* Product Information */}
        <div className="product-info">
          <h2 className="product-title">{product.name}</h2>
          <p className="product-field">
            <NodeIndexOutlined className="icon" />
            <strong>SKU:</strong> {product.sku || "N/A"}
          </p>

          <p className="product-field" onClick={handleBarcodeUpdate}>
            <BarcodeOutlined className="icon" />
            <strong>Barcode:</strong> {product.barcode || "N/A"}
          </p>

          <p className="product-field" onClick={handleWeightUpdate}>
            <EditOutlined className="icon" />
            <strong>Weight:</strong> {product.weight} kg
          </p>

          <p className={`product-stock ${product.qty_available > 0 ? "stock-available" : "stock-out"}`}>
            <strong>Stock:</strong> {product.qty_available} {product.uom}
          </p>

          {product.description && (
            <p className="product-description">
              <strong>Description:</strong> {product.description}
            </p>
          )}
        </div>
      </Card>

        <Button type="primary" onClick={() => navigate(`/stock/${product.id}`)} className="stock-button">
          View Stock List
        </Button>
        <br />
        <Button type="primary" onClick={() => navigate(`/product/${product.id}/packaging`)}>
          View Packaging
        </Button>
    </div>
  );
}

export default ProductView;
