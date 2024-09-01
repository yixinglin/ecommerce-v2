from core.log import logger
from .base import OdooAPIKey, OdooAPIBase

class OdooOrderAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_order_ids(self):
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

    def create_order(self, quot_data):
        logger.info(f"Creating order with data: {quot_data}")
        self.client.create('sale.order', [quot_data])
