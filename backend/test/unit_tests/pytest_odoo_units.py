import unittest
from core.log import logger
from services.odoo import OdooInventoryService, OdooContactService, OdooProductService


class TestOdooUnits(unittest.TestCase):

    def setUp(self):
        pass

    def test_inventory(self):
        logger.info("Testing inventory")
        with OdooInventoryService(key_index=0) as svc:
            svc.save_all_internal_locations()
            svc.save_all_quants()
            svc.save_all_putaway_rules()

        with OdooProductService(key_index=0) as svc:
            svc.save_all_product_templates()
            svc.save_all_products()

        with OdooContactService(key_index=0) as svc:
            svc.save_all_contacts()



if __name__ == '__main__':
    unittest.main()