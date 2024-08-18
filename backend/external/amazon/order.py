from datetime import timedelta
from sp_api.api import Orders
from sp_api.base import Marketplaces
from core.log import logger
from .base import AmazonSpAPIKey, today


class AmazonOrderAPI:
    """
    This class represents the Amazon Sp API and provides methods to fetch orders and order items
    """
    def __init__(self, api_key: AmazonSpAPIKey, marketplace: Marketplaces):
        """
        Initializes the AmazonOrderAPI object with the provided API key and marketplace
        :param api_key:  Key to access the Amazon Sp API
        :param marketplace: Marketplace e.g. Marketplaces.DE
        """
        self.key: AmazonSpAPIKey = api_key
        self.marketplace: Marketplaces = marketplace
        credentials = self.key.__dict__
        self.orderClient = Orders(credentials=credentials, marketplace=self.marketplace)
        self.salesChannel = f"Amazon.{self.marketplace.name.lower()}"

    def get_account_id(self):
        return self.key.get_account_id()

    def fetch_all_orders(self, days_ago=30, **kwargs):
        """
        Fetches all orders from the Amazon Sp API for the specified marketplace and account.
        :param days_ago:  Number of days to fetch orders from (default 30)
        :param kwargs:   Additional arguments to pass to the get_orders method of the Orders API
        :return:   List of orders
        """
        # Calculate the start date based on the specified days ago
        start_date = (today() - timedelta(days=days_ago)).isoformat()
        # Fetch the initial set of orders based on the start date and any additional kwargs
        logger.info(f"[API] Fetching orders since {start_date}")
        response = self.orderClient.get_orders(CreatedAfter=start_date, **kwargs)
        orders = response.Orders  # Get the initial set of orders
        # Retrieve additional orders while there is a next page of results
        while response.NextToken:
            logger.info(f"[API] Fetching additional orders [{response.NextToken}]")
            response = self.orderClient.get_orders(CreatedAfter=start_date, NextToken=response.NextToken, **kwargs)
            orders.extend(response.Orders)  # Add the additional orders to the list
        return orders

    def fetch_order(self, order_id):
        """
        Fetches the details of an Amazon order by its ID.
        :param order_id:  ID of the Amazon order to fetch
        :return:   Details of the Amazon order
        """
        result = self.orderClient.get_order(order_id)
        logger.info(f"[API] Fetching Amazon order {order_id} updated at {result.payload['LastUpdateDate']}")
        return result

    def fetch_order_items(self, order_id):
        """
        Fetches the items of an Amazon order by its ID.
        :param order_id:  ID of the Amazon order to fetch items for
        :return:   List of items in the Amazon order
        """
        logger.info(f"[API] Fetching Amazon items for order [{order_id}]")
        return self.orderClient.get_order_items(order_id)

