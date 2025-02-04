from typing import Optional

from pydantic import BaseModel, Field

from core.log import logger
from .base import OdooAPIKey, OdooAPIBase

class ProductUpdate(BaseModel):
    id: int
    weight: Optional[float] = Field(default=None, gt=0)
    barcode: Optional[str] = Field(default=None, min_length=1)
    image_1920: Optional[str] = Field(default=None, min_length=1)

class OdooProductAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_product_template_ids(self, domain=[]):
        logger.info("Fetching product template ids")
        # Note: Fetch product template excludes inactive templates by default.
        domain += [('active', 'in', [True, False])]
        product_templ_ids = self.client.search('product.template', [domain])
        return product_templ_ids

    def fetch_product_templates_by_ids(self, ids):
        """
        Fetch product templates by ids. The result is a list of dictionaries not including product variants.
        :param ids:
        :return:
        """
        logger.info("Fetching product template by ids")
        return self.client.read('product.template', [ids], {})

    def fetch_product_template_write_date(self, ids):
        return self.fetch_write_date("product.template", ids)

    def fetch_product_ids(self, domain=[]):
        logger.info("Fetching product ids")
        domain += [('active', 'in', [True, False])]
        product_ids = self.client.search('product.product', [domain])
        return product_ids

    def fetch_products_by_ids(self, ids):
        """
        Fetch product by ids. The result is a list of dictionaries including product variants.
        :param ids:
        :return:
        """
        logger.info("Fetching product ids")
        return self.client.read('product.product', [ids], {})

    def fetch_product_write_date(self, ids):
        return self.fetch_write_date("product.product", ids)

    def update_product_by_id(self, id: int, data: ProductUpdate):
        values_to_update = {}
        if data.weight:
            if data.weight <= 0 or data.weight > 1000:
                raise ValueError("Weight should be between 0 and 1000")
            values_to_update['weight'] = data.weight
        if data.barcode:
            values_to_update['barcode'] = data.barcode
        if data.image_1920:
            values_to_update['image_1920'] = data.image_1920
        result = self.client.write('product.product', [[id], values_to_update])
        if result:
            logger.info(f"Updated product {id} with data {data}")
        else:
            logger.error(f"Failed to update product {id} with data {data}")
        return result

class PackagingUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(default=None, min_length=1)
    barcode: Optional[str] = Field(default=None, min_length=1)
    qty: Optional[float] = Field(default=None, gt=0)


class OdooProductPackagingAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_packaging_ids(self, domain=[]):
        logger.info("Fetching packaging ids")
        packaging_ids = self.client.search('product.packaging', [domain])
        return packaging_ids

    def fetch_packaging_by_ids(self, ids):
        logger.info("Fetching packaging by ids")
        return self.client.read('product.packaging', [ids], {})

    def fetch_packaging_write_date(self, ids):
        return self.fetch_write_date("product.packaging", ids)

    def update_packaging_by_id(self, id: int, data: PackagingUpdate):
        values_to_update = {}
        if data.name:
            values_to_update['name'] = data.name
        if data.barcode:
            values_to_update['barcode'] = data.barcode
        if data.qty:
            values_to_update['qty'] = data.qty
        result = self.client.write('product.packaging', [[id], values_to_update])
        if result:
            logger.info(f"Updated packaging {id} with data {data}")
        else:
            logger.error(f"Failed to update packaging {id} with data {data}")
        return result