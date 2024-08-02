"""
Test the integration layer of Amazon
"""
import json
import logging
import unittest
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_source():
    with open("test/source.json") as f:
        source = json.load(f)
    return source


class TestAmazonIntegration(unittest.TestCase):

    def setUp(self):
        """
        Set up the test environment
        :return:
        """
        source = load_source()
        self.base_url = source['urls'].get('test_env_url')
        self.base_order_url = f"{self.base_url}/api/v1/amazon/orders"
        logger.info("Testing Amazon Integration")


    def test_get_orders(self):
        """
        Test the get_orders function
        """
        logger.info("Testing get_orders function")
        params = dict(days_ago=3,  limit=300, offset=0, api_key_index=0)
        response = requests.get(self.base_order_url,
                                params=params)
        data = response.json()
        orders = data.get("data").get("orders")
        size = data.get("data").get("size")

        logger.info("Message: %s", data.get("message"))
        logger.info("#Orders: %s", size)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("code"), "200")
        self.assertEqual(len(orders), size)
        logger.info(f"Sample Order Number: {orders[0].get('orderId')}")
        logger.info("Test get_amazon_orders function passed\n")


    def test_get_unshipped_orders(self):
        """
        Test the get_unshipped_orders function
        """
        logger.info("Testing get_unshipped_orders function")
        params = dict(up_to_date=False, api_key_index=0, country='DE')
        url = f"{self.base_order_url}/unshipped"
        response = requests.get(url,
                                params=params)
        data = response.json()
        orderNumbers = data.get("data").get("orderNumbers")
        length = data.get("data").get("length")

        logger.info("Message: %s", data.get("message"))
        logger.info("#Unshipped Orders: %s", length)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("code"), "200")
        self.assertEqual(len(orderNumbers), length)
        logger.info(f"Sample Order Number: {orderNumbers[0]}")
        logger.info("Test get_unshipped_orders function passed\n")

    def test_order_items_count(self):
        """
        Test the order_items_count function
        """
        logger.info("Testing order_items_count function")
        days_ago = 3
        url = f"{self.base_order_url}/ordered-items-count/daily/{days_ago}"
        response = requests.get(url)
        data = response.json()
        message = data.get("message")
        items = data.get("data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get("code"), "200")
        logger.info(f"Message: {message}")
        logger.info(f"Sample Item: {items[0]['dailyShipments'][0]['sellerSKU']}")

        logger.info("Test order_items_count function passed\n")


class TestAmazonPickPackService(unittest.TestCase):

    def setUp(self):
        source = load_source()
        self.base_url = source['urls'].get('test_env_url')
        self.base_pick_pack_url = f"{self.base_url}/api/v1/pickpack/amazon"
        logger.info("Testing Amazon Pick Pack Service")

    def test_download_unshipped_orders_to_pick(self):
        # "/api/v1/pickpack/amazon/batch-pick/unshipped"
        logger.info("Testing download_unshipped_orders_to_pick function")
        params = dict(up_to_date=False, days_ago=3, api_key_index=0)
        url = f"{self.base_pick_pack_url}/batch-pick/unshipped"

        response = requests.get(url, params=params)
        data = response.content
        self.assertEqual(response.status_code, 200)
        # Save to excel file
        with open('.temp/orders-to-pick.xlsx', 'wb') as f:
            f.write(data)
        logger.info("Test download_unshipped_orders_to_pick function passed\n")


    def test_download_unshipped_orders_to_pack(self):
        # "/api/v1/pickpack/amazon/batch-pack/unshipped"
        logger.info("Testing download_unshipped_orders_to_pack function")
        params = dict(up_to_date=False, days_ago=3, api_key_index=0)
        url = f"{self.base_pick_pack_url}/batch-pack/unshipped"

        response = requests.get(url, params=params)
        data = response.content
        self.assertEqual(response.status_code, 200)
        # Save to Excel file
        with open('.temp/orders-to-pack.xlsx', 'wb') as f:
            f.write(data)
        logger.info("Test download_unshipped_orders_to_pack function passed\n")


if __name__ == '__main__':
    unittest.main()