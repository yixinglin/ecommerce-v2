-- alias = fields.CharField(max_length=50, default="", unique=True, description="Alias for this SKU")

ALTER TABLE ecommerce_api.lx_sku_replenishment_profile
    ADD alias varchar(50) COMMENT 'Alias for this SKU'
    AFTER local_sku;

ALTER TABLE ecommerce_api.lx_sku_replenishment_profile
    ADD CONSTRAINT alias UNIQUE KEY (alias);

-- units_per_fba_carton = fields.IntField(default=1, description="Number of units per FBA carton")
ALTER TABLE ecommerce_api.lx_sku_replenishment_profile
    ADD units_per_fba_carton INT
    DEFAULT 1 NOT NULL COMMENT 'Number of units per FBA carton'
    AFTER units_per_carton;