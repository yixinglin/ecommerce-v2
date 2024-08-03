import unittest
from unittest.mock import MagicMock

from external.amazon.base import AmazonSpAPIKey
from external.amazon.product import AmazonCatalogAPI
from sp_api.base import Marketplaces





class TestAmazonCatalogAPI(unittest.TestCase):

    def test_get_catalog_item_happy_path(self):
        # Mock the AmazonSpAPIKey.from_json method
        api_key_mock = AmazonSpAPIKey.from_json()

        # Mock the Catalog client and its get_item method
        catalog_client_mock = MagicMock()
        catalog_client_mock.get_item = MagicMock(return_value=MagicMock(payload={'asin': '12345', 'name': 'Product 1'}))

        # Create an instance of AmazonCatalogAPI with mocked objects
        api = AmazonCatalogAPI(api_key=api_key_mock, marketplace=Marketplaces.DE)
        api.catalogClient = catalog_client_mock  # Replace the catalogClient with the mocked one

        # Call the get_catalog_item method
        result = api.fetch_catalog_item('12345')

        # Assert that the correct item is returned
        self.assertEqual(result, {'asin': '12345', 'name': 'Product 1'})

    def test_get_catalog_item_invalid_asin(self):
        # Mock the AmazonSpAPIKey.from_json method
        api_key_mock = MagicMock()
        AmazonSpAPIKey.from_json = MagicMock(return_value=api_key_mock)

        # Mock the Catalog client and its get_item method
        catalog_client_mock = MagicMock()
        catalog_client_mock.get_item = MagicMock(return_value=MagicMock(payload=None))

        # Create an instance of AmazonCatalogAPI with mocked objects
        api = AmazonCatalogAPI(api_key=api_key_mock, marketplace=Marketplaces.US)
        api.catalogClient = catalog_client_mock  # Replace the catalogClient with the mocked one

        # Call the get_catalog_item method with an invalid ASIN
        result = api.fetch_catalog_item('invalid_asin')

        # Assert that the result is None
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
