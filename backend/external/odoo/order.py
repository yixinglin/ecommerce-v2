from core.log import logger
from .base import OdooAPIKey, OdooAPIBase


class OdooOrderAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_order_ids(self):
        pass

    def fetch_orderline_ids(self):
        pass

    # def make_quot_data():
    #     quotation_data = {
    #         'partner_id': 1632,  # 客户ID（必填）
    #         'order_line': [],  # 订单行信息（稍后添加）
    #     }
    #     # 设置订单行信息
    #     order_line_data = [
    #         (0, 0, {
    #             'product_id': 885,  # 产品ID（必填） model: product.product
    #             'product_uom_qty': 2,  # 产品数量
    #             'price_unit': 100.0,  # 单价
    #         }),
    #         (0, 0, {
    #             'product_id': 881,  # 产品ID（必填）
    #             'product_uom_qty': 3,  # 产品数量
    #             'price_unit': 150.0,  # 单价
    #         }),
    #     ]
    #     quotation_data['order_line'] = order_line_data
    #     return quotation_data

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
        # fields = {
        #     "fields": ['name', 'complete_name', 'origin', 'partner_id', 'create_date', ]
        # }
        orders = self.client.search_read('stock.picking', [domain])
        return orders