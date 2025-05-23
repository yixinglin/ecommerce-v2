from sp_api.api import Catalog, CatalogItems
from sp_api.base import Marketplaces
from core.log import logger
from external.amazon.base import AmazonSpAPIKey


class AmazonCatalogAPI:
    def __init__(self, api_key: AmazonSpAPIKey,
                 marketplace: Marketplaces):
        """
        Initialize Amazon Catalog API client
        :param api_key:  Amazon Sp API key
        :param marketplace:  Amazon marketplace, e.g. Marketplaces.DE
        """
        self.key: AmazonSpAPIKey = api_key
        self.marketplace: Marketplaces = marketplace
        credentials = self.key.__dict__
        self.catalogClient = Catalog(credentials=credentials,
                                     marketplace=self.marketplace)
        self.catalogItmesClient = CatalogItems(credentials=credentials,
                                               marketplace=self.marketplace)

    def fetch_catalog_item(self, asin: str):
        """
        Get catalog item for given ASIN
        :param asin:  ASIN of the product
        :return: Catalog item for given ASIN
        """
        logger.info(f"[API] Fetching Amazon catalog item for ASIN: {asin}")
        result = self.catalogClient.get_item(asin=asin)
        item = result.payload
        return item
