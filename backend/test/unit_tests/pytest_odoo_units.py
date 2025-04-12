import unittest
from typing import List
from unittest.mock import MagicMock

from core.log import logger
from models.orders import StandardProduct
from services.odoo import OdooInventoryService, OdooContactService, OdooProductService
from services.odoo.OdooDashboardService import OdooOrderDashboardService
from services.odoo.OdooOrderService import OdooProductPackagingService, OdooOrderService


class TestOdooUnits(unittest.TestCase):

    def setUp(self):
        pass

    def test_order(self):
        with OdooOrderService(key_index=1, login=False) as svc:
            order_lines = svc.query_orderlines_by_salesman_id([7])
            assert len(order_lines) > 0
            logger.info(f"Found {len(order_lines)} order lines")

        with OdooOrderDashboardService(key_index=1, login=False) as svc:
            data = svc.stats_sales_order_by_salesman(salesman_ids=[7])
            data = svc.stats_sales_order_by_customer()



    def test_product(self):
        with OdooProductService(key_index=0) as svc:
            products1: StandardProduct = svc.query_product_by_code("AM-091564")
            assert products1.code == "AM-091564"
            logger.info(f"Found product {products1.code}")

            id = int(products1.id)
            product2: StandardProduct = svc.query_product_by_id(id)
            assert product2.code == "AM-091564"
            logger.info(f"Found product {product2.code} by id")

            products3: List[StandardProduct] = svc.query_all_products(offset=10, limit=10)
            assert len(products3) > 0
            logger.info(f"Found {len(products3)} products")

            product_templates: StandardProduct = svc.query_all_product_templates(offset=10, limit=10)
            assert len(product_templates) > 0
            logger.info(f"Found {len(product_templates)} product templates")

    def test_packaging(self):
        with OdooProductPackagingService(key_index=1) as svc:
            data = svc.query_all_product_packaging(offset=10, limit=10)
            packagings = data["packagings"]
            assert len(packagings) > 0
            logger.info(f"Found {len(packagings)} product packagings")

            id = int(packagings[0]['data']["id"])
            packaging = svc.query_packaging_by_id(id)
            assert packaging["qty"] == packagings[0]['data']["qty"]
            logger.info(f"Found product packaging {packaging['name']} by id")

    def test_contect(self):
        with OdooContactService(key_index=0) as svc:
            data = svc.query_all_contacts(offset=10, limit=10)
            contacts1 = data["contacts"]
            assert len(contacts1) > 0
            logger.info(f"Found {len(contacts1)} contacts")

            id = int(contacts1[0]['contact']["id"])
            contact2: dict = svc.query_contact_by_id(id)
            assert contact2["name"] == contacts1[0]['contact']["name"]
            logger.info(f"Found contact {contact2['name']} by id")


class TestOdooUnits2(unittest.TestCase):

    def setUp(self):
        pass

    # def test_saving(self):
    #     logger.info("Testing inventory")
    #     with OdooInventoryService(key_index=0) as svc:
    #         svc.save_all_internal_locations()
    #         svc.save_all_quants()
    #         svc.save_all_putaway_rules()
    #
    #     with OdooProductService(key_index=0) as svc:
    #         svc.save_all_product_templates()
    #         svc.save_all_products()
    #
    #     with OdooContactService(key_index=0) as svc:
    #         svc.save_all_contacts()
    #
    #     with OdooProductPackagingService(key_index=0) as svc:
    #         svc.save_all_product_packaging()

    def test_saving_2(self):
        logger.info("Testing Order")
        with OdooOrderService(key_index=0) as svc:
            svc.save_all_orderlines()


if __name__ == '__main__':
    unittest.main()