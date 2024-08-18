from core.log import logger
from .base import OdooAPIKey, OdooAPIBase

class OdooOrderAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey):
        super().__init__(api_key)

    def fetch_order_ids(self):
        pass