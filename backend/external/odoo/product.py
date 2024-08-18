from core.log import logger
from .base import OdooAPIKey, OdooAPIBase


class OdooProductAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey):
        super().__init__(api_key)

    def fetch_product_template_ids(self, domain=[]):
        logger.info("Fetching product template ids")
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
