"""
Model List:
- stock.location: This model is used to manage locations.
- stock.putaway.rule: This model is used to define rules for putting away products.
- stock.quant: This model is used to manage the inventory of products. Each stock.quant record represents the quantity of a specific product available at a specific location within the warehouse.
"""

from core.log import logger
from .base import OdooAPIKey, OdooAPIBase


class OdooInventoryAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_location_ids(self, domain=[]):
        logger.info("Fetching location ids")
        domain += [('active', 'in', [True, False])]
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
        domain += [('active', 'in', [True, False])]
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

    def request_quant_by_id(self, quant_id, inv_quantity) -> bool:
        logger.info(f"Requesting quant_inventory by id {quant_id} with quantity {inv_quantity}")
        return self.client.write('stock.quant', [[quant_id],
                {'inventory_quantity': inv_quantity}])

    def quant_relocation_by_id(self, quant_id, location_id, message) -> bool:
        logger.info(f"Relocating quant_inventory by id {quant_id} to location {location_id}")
        # 创建移库
        quant_ids = [quant_id]
        relocate_id = self.client.create('stock.quant.relocate', [{
            'quant_ids': [(6, 0, quant_ids)],  # 选中要移动的库存
            'dest_location_id': location_id,  # 目标位置
            'message': message,  # 备注
        }])

        if relocate_id:
            return self.client.execute_kw('stock.quant.relocate', 'action_relocate_quants', [[relocate_id]])
        else:
            return False

    def create_putaway_rule(self, product_id, location_out_id, location_in_id=8) -> int:
        logger.info(f"Creating putaway rule for product {product_id} "
                    f"from location {location_in_id} to location {location_out_id}")
        putaway_rule_data = {
            'location_in_id': location_in_id,
            'location_out_id': location_out_id,
            'product_id': product_id,
        }
        return self.client.create('stock.putaway.rule', [putaway_rule_data])

    def update_putaway_rule(self, rule_id, location_out_id, location_in_id=8) -> bool:
        logger.info(f"Updating putaway rule {rule_id} with location_out_id {location_out_id} and location_in_id {location_in_id}")
        return self.client.write('stock.putaway.rule', [[rule_id],
                     {'location_in_id': location_in_id,
                      'location_out_id': location_out_id}])



