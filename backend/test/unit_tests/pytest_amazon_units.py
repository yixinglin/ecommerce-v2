import logging
import unittest
from typing import List
import requests
from sp_api.base import Marketplaces
from core.db import OrderQueryParams
from models.orders import StandardOrder
from services.amazon.AmazonService import AmazonOrderService, AmazonCatalogService
from services.amazon.bulkOrderService import AmazonBulkPackSlipDE
import json

import utils.address as city_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAmazonUnits(unittest.TestCase):

    def setUp(self):
        logger.info("Testing Amazon Units")
        with open("test/source.json") as f:
            self.source = json.load(f)

    def test_query_orders(self):
        logger.info("Testing query_orders")
        with AmazonOrderService(0,
                marketplace=Marketplaces.DE) as svc:
            params = OrderQueryParams()
            params.purchasedDateFrom = "2024-05-01T01:14:51Z"
            params.purchasedDateTo = "2024-08-31T23:59:59Z"
            params.status = ["Canceled"]
            orders = svc.find_orders_by_query_params(params)
            logger.info(f"Found {params.status} {len(orders)} orders")
            for order in orders:
                self.assertEqual(order.status, "Canceled")

            filter_ = {"order.OrderStatus": "Unshipped",
                       "order.FulfillmentChannel": "MFN"}
            orders = svc.find_orders(offset=0, limit=100, filter=filter_)
            logger.info(f"Found {len(orders)} orders with filter {filter_}")
            for order in orders:
                self.assertEqual(order.status, "Unshipped")

            orderId = orders[0].orderId
            logger.info(f"Found order {orderId}")
            order = svc.find_order_by_id(orderId)
            self.assertEqual(order.orderId, orderId)

            orderId = "303-3875440-9470748" # "305-6648619-7627559" 303-3875440-9470748
            # svc.save_order(order_id=orderId)

        logger.info("Testing query_orders passed")

    def test_catalog(self):
        logger.info("Testing catalog")
        with AmazonCatalogService(0, marketplace=Marketplaces.DE) as svc:
            catalog_map = svc.create_asin_image_url_dict()
            catalog_items = catalog_map.keys()
            logger.info(f"Found {len(catalog_items)} catalog items")
            catalog_item = svc.query_catalog_item('B0CPSMQW95')
            svc.save_catalog("B0CPSMQW95")
            cnt = svc.remove_catalog_item("B0CPSMQW95")
            self.assertEqual(cnt, 1)


        logger.info("Testing catalog passed")

    def test_parse_pack_slip_page(self):
        logger.info("Testing parse_pack_slip_page")
        url = self.source['urls']["amazon_pack_slip_page"]
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content
        bulkOrderService = AmazonBulkPackSlipDE(content)
        ids = bulkOrderService.get_order_ids()
        items = bulkOrderService.get_order_items()
        addresses = bulkOrderService.get_shipping_addresses()

        logger.info(f"#Odder IDs: {len(ids)}")
        logger.info(f"#Items: {len(items)}")
        logger.info(f"#Addresses: {len(addresses)}")

        self.assertEqual(len(ids), 200)

        orders: List[StandardOrder] = bulkOrderService.extract_all()
        map_id_to_order = {order.orderId: order for order in orders}
        sample = map_id_to_order["028-8771620-3087536"]
        self.assertEqual(sample.orderId, "028-8771620-3087536")
        self.assertEqual(sample.shipAddress.zipCode, "65520")
        self.assertEqual(sample.shipAddress.street1, "Lisztstraße 3a")

        sample = map_id_to_order["306-4612375-0894748"]
        self.assertEqual(sample.orderId, "306-4612375-0894748")
        self.assertEqual(sample.shipAddress.zipCode, "24966")
        self.assertEqual(sample.shipAddress.street1, "Winderatt 24")

        sample = map_id_to_order["305-9455165-8661158"]
        self.assertEqual(sample.orderId, "305-9455165-8661158")
        self.assertEqual(sample.shipAddress.zipCode, "50733")
        self.assertEqual(sample.shipAddress.street1, "Neusser Str. 301")
        self.assertEqual(sample.shipAddress.name2, "Nippiser Kiosk")

        sample = map_id_to_order["305-9115966-2695521"]
        self.assertEqual(sample.orderId, "305-9115966-2695521")
        self.assertEqual(sample.shipAddress.zipCode, "06110")
        self.assertEqual(sample.shipAddress.street1, "Niemeyerstraße 23")
        self.assertEqual(sample.shipAddress.name2, "4 Stock")

        sample = map_id_to_order["304-4933793-4427540"]
        self.assertEqual(sample.orderId, "304-4933793-4427540")
        self.assertEqual(sample.shipAddress.zipCode, "80539")
        self.assertEqual(sample.shipAddress.street1, "Von Der Tann Straße 12")
        self.assertTrue("Czarnota" in sample.shipAddress.name2)
        self.assertTrue("GmbH" in sample.shipAddress.name1)
        self.assertTrue("Rückgebäude" in sample.shipAddress.name3)

        for order in orders:
            street = order.shipAddress.street1
            streetName, houseNumber = city_utils.identify_german_street(street)
            # logger.info(f"Order {order.orderId} has street {street} identified as {streetName} + {houseNumber}")


        logger.info("Testing parse_pack_slip_page passed")



if __name__ == '__main__':
    unittest.main()
