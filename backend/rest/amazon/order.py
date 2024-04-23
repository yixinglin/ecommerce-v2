from datetime import timedelta
from typing import Tuple
from sp_api.api import Orders
from sp_api.base import Marketplaces
from core.log import logger
from .base import AmazonSpAPIKey, today


# This class represents the Amazon Sp API and provides methods to fetch orders and order items
class AmazonOrderAPI:
    def __init__(self, api_key: AmazonSpAPIKey=AmazonSpAPIKey.from_json(), marketplace=Marketplaces.DE):
        self.key: AmazonSpAPIKey = api_key
        self.marketplace: Tuple = marketplace
        credentials = self.key.__dict__
        self.orderClient = Orders(credentials=credentials, marketplace=self.marketplace)

    def get_all_orders(self, days_ago=30, **kwargs):
        # Calculate the start date based on the specified days ago
        start_date = (today() - timedelta(days=days_ago)).isoformat()
        # Fetch the initial set of orders based on the start date and any additional kwargs
        logger.info(f"Fetching orders since {start_date}")
        response = self.orderClient.get_orders(CreatedAfter=start_date, **kwargs)
        orders = response.Orders  # Get the initial set of orders
        # Retrieve additional orders while there is a next page of results
        while response.NextToken:
            logger.info(f"Fetching additional orders [{response.NextToken}]")
            response = self.orderClient.get_orders(CreatedAfter=start_date, NextToken=response.NextToken, **kwargs)
            orders.extend(response.Orders)  # Add the additional orders to the list
        return orders

    def get_order(self, order_id):
        result = self.orderClient.get_order(order_id)
        logger.info(f"Fetching order {order_id} updated at {result.payload['LastUpdateDate']}")
        return result

    def get_order_items(self, order_id):
        logger.info(f"Fetching items for order [{order_id}]")
        return self.orderClient.get_order_items(order_id)
