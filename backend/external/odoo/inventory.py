"""
Model List:
- stock.location: This model is used to manage locations.
- stock.putaway.rule: This model is used to define rules for putting away products.
- stock.quant: This model is used to manage the inventory of products. Each stock.quant record represents the quantity of a specific product available at a specific location within the warehouse.
"""

from core.log import logger
from .base import OdooAPIKey, OdooAPIBase


class OdooInventoryAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey):
        super().__init__(api_key)

    def fetch_location_ids(self, domain=[]):
        logger.info("Fetching location ids")
        return self.client.search('stock.location', [domain])

    def fetch_location_by_ids(self, ids):
        logger.info("Fetching internal locations by ids")
        return self.client.read('stock.location', [ids])

    def fetch_internal_location_ids(self):
        return self.fetch_location_ids(domain=[('usage', '=', 'internal')])

    def fetch_location_by_complete_name(self, name):
        return self.fetch_location_ids(domain=[('complete_name', '=', name)])

    def fetch_location_write_date(self, ids):
        return self.fetch_write_date('stock.location', ids)

    def fetch_putaway_rule_ids(self, domain = []):
        logger.info("Fetching putaway rule ids")
        return self.client.search('stock.putaway.rule', [domain])

    def fetch_putaway_rule_by_ids(self, ids):
        logger.info("Fetching putaway rules by ids")
        return self.client.read('stock.putaway.rule', [ids])

    def fetch_putaway_rule_write_date(self, ids):
        return self.fetch_write_date('stock.putaway.rule', ids)

    def fetch_quant_ids(self, domain=[]):
        """
        This method fetches all the quant ids from the stock.quant model.
        "Quant" represents the quantity of a specific product available at a specific location within the warehouse.
        :return:
        """
        logger.info("Fetching quant ids")
        domain0 = [('location_id', 'ilike', "WH/Stock"),  # contains WH/Stock
                  ]
        domain = domain0 + domain
        return self.client.search('stock.quant', [domain])

    def fetch_quant_by_ids(self, ids):
        logger.info("Fetching quants by ids")
        return self.client.read('stock.quant', [ids])

    def fetch_quant_by_product_location(self, product_id, location_id):
        logger.info("Fetching quant by product and location")
        domain = [('product_id', '=', product_id),
                  ('location_id', '=', location_id),
                  ]
        return self.client.search_read('stock.quant', [domain], {})

    def fetch_quant_write_date(self, ids,):
        return self.fetch_write_date('stock.quant', ids)


