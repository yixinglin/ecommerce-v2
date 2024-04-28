from typing import Tuple

from sp_api.api import Catalog
from sp_api.base import Marketplaces

from core.log import logger
from .base import AmazonSpAPIKey


class AmazonCatalogAPI:
    def __init__(self, api_key: AmazonSpAPIKey = AmazonSpAPIKey.from_json(),
                 marketplace: Tuple = Marketplaces.DE):
        self.key: AmazonSpAPIKey = api_key
        self.marketplace: Tuple = marketplace
        credentials = self.key.__dict__
        self.catalogClient = Catalog(credentials=credentials,
                                     marketplace=self.marketplace)

    def get_catalog_item(self, asin: str):
        """
        Get catalog item for given ASIN
        :param asin:  ASIN of the product
        :return: Catalog item for given ASIN
        """
        logger.info(f"Fetching Amazon catalog item for ASIN: {asin}")
        result = self.catalogClient.get_item(asin=asin)
        item = result.payload
        return item
