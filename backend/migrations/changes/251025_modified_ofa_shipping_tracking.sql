--class ShippingTrackingModel(TortoiseBasicModel):
--    id = fields.BigIntField(pk=True)
--    order_id = fields.BigIntField(description="Associated order ID")
--    tracking_number = fields.CharField(max_length=64, description="Tracking number")
--    carrier_code = fields.CharField(max_length=32, description="Carrier code (e.g., SF, UPS)")
--    location = fields.CharField(max_length=50, null=True, description="Current location of the package, e.g. Hamburg, Berlin")
--    country_code = fields.CharField(max_length=8, description="ISO country code (e.g., US, CN)")
--    description = fields.CharField(max_length=512, null=True, description="Description of the package")
--    status_text = fields.CharField(max_length=64, description="Latest status (e.g., Delivered, In Transit)")
--    raw_data = fields.JSONField(null=True, description="Raw tracking payload or history")
--
--    class Meta:
--        table = "ofa_shipping_tracking"
--        unique_together = (("tracking_number", "carrier_code"),)


CREATE TABLE `ofa_shipping_tracking` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Creation timestamp',
  `created_by` varchar(20) DEFAULT NULL COMMENT 'Creator name',
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Last updated timestamp',
  `updated_by` varchar(20) DEFAULT NULL COMMENT 'Last updater name',
  `order_id` bigint NOT NULL COMMENT 'Associated order ID',
  `tracking_number` varchar(64) NOT NULL COMMENT 'Tracking number',
  `carrier_code` varchar(32) NOT NULL COMMENT 'Carrier code (e.g., SF, UPS)',
  `location` varchar(50) DEFAULT NULL COMMENT 'Current location of the package, e.g. Hamburg, Berlin',
  `country_code` varchar(8) NOT NULL COMMENT 'ISO country code (e.g., US, CN)',
  `description` varchar(512) DEFAULT NULL COMMENT 'Description of the package',
  `status_text` varchar(64) NOT NULL COMMENT 'Latest status (e.g., Delivered, In Transit)',
  `raw_data` json DEFAULT NULL COMMENT 'Raw tracking payload or history',
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_id` (`order_id`),
  UNIQUE KEY `uid_ofa_shippin_trackin_65020d` (`tracking_number`,`carrier_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


--OrderModel
--冗余字段delivered
ALTER TABLE ofa_orders
ADD COLUMN delivered BOOL DEFAULT 0 NOT NULL
COMMENT 'Whether the package has been delivered' AFTER thumbnails;
