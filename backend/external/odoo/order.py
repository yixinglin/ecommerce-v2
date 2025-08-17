from core.log import logger
from .base import OdooAPIKey, OdooAPIBase


class OdooOrderAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_order_ids(self):
        raise NotImplementedError()

    def fetch_orderline_ids(self):
        domain = [('salesman_id', 'not in', [8, 6])]
        return self.client.search('sale.order.line', [domain])

    def fetch_orderline_by_ids(self, ids):
        fields = ['order_id', 'name', 'currency_id', 'order_partner_id', 'salesman_id', 'product_template_id',
                  'state', 'product_uom', 'product_uom_qty', 'product_qty', 'price_unit',
                  'price_subtotal', 'price_tax', 'price_total', 'qty_to_invoice', 'qty_to_deliver',
                  'product_type', 'create_date', 'is_delivery', 'display_type', 'discount'
                  ]
        return self.client.read('sale.order.line', [ids], {"fields": fields})

    def fetch_ordered_product_ids(self):
        logger.info("Fetching ordered product ids")
        domain = [('state', '=', 'sale'), ('product_type', '=', 'product')]
        fields = {
            "fields": ['product_id']
        }
        res = self.client.search_read('sale.order.line', [domain], fields)
        product_ids = [item['product_id'][0] for item in res]
        product_ids = list(set(product_ids))
        return product_ids

    def create_sales_order(self, quot_data):
        logger.info(f"Creating order with data: {quot_data}")
        self.client.create('sale.order', [quot_data])

    def fetch_delivery_order(self, order_number):
        domain = [('picking_type_id', '=', 2),
                  ('state', '!=', ['cancel']),
                  ('name', '=', order_number),
                  ('is_return_picking', '=', False)]
        orders = self.client.search_read('stock.picking', [domain])
        return orders