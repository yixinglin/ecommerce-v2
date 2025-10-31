--已导入 10.31
ALTER TABLE ecommerce_api.ofa_shipping_labels MODIFY COLUMN tracking_id varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT 'Logistics tracking ID';
ALTER TABLE ecommerce_api.ofa_shipping_labels MODIFY COLUMN tracking_number varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'Logistics tracking number';
ALTER TABLE ecommerce_api.ofa_orders ADD parcel_weights varchar(128) NULL COMMENT 'Parcel weights (in kg)' AFTER delivered;


-- 11.2 新增字段
ALTER TABLE ecommerce_api.ofa_orders ADD tracking_info varchar(512) NULL COMMENT 'Logistics tracking info' after tracking_url;
