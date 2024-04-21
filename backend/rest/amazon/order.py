import os
from datetime import timedelta, datetime
from typing import Tuple

from sp_api.api import Orders
from sp_api.base import Marketplaces
from core.config import settings
import json
from core.log import logger

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'


def now():
    return datetime.now().strftime(DATETIME_PATTERN)


def today():
    return datetime.now().date()


# This class represents the Amazon Sp API keys and provides methods to fetch orders and order items
class AmazonSpAPIKey:
    def __init__(self):
        self.refresh_token: str = None
        self.lwa_app_id: str = None
        self.lwa_client_secret: str = None
        self.aws_access_key: str = None
        self.aws_secret_key: str = None
        self.role_arn: str = None

    @classmethod
    def from_json(cls):
        # Load the API keys from the JSON file
        file_path = os.path.join('conf', 'apikeys',
                                 settings.AMAZON_ACCESS_KEY)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = AmazonSpAPIKey()
        k.__dict__.update(data)
        return k


# This class represents the Amazon Sp API and provides methods to fetch orders and order items
class AmazonOrderAPI:
    def __init__(self, api_key=AmazonSpAPIKey.from_json(), marketplace=Marketplaces.DE):
        self.key: AmazonSpAPIKey = api_key
        self.marketplace: Tuple = marketplace
        credentials = self.key.__dict__
        self.orderClient = Orders(credentials=credentials, marketplace=self.marketplace)

    def get_all_orders(self, days_ago=30, **kwargs):
        # Calculate the start date based on the specified days ago
        start_date = (today() - timedelta(days=days_ago)).isoformat()
        # Fetch the initial set of orders based on the start date and any additional kwargs
        logger.info(f"Fetching additional orders since {start_date}")
        response = self.orderClient.get_orders(CreatedAfter=start_date, **kwargs)
        orders = response.Orders  # Get the initial set of orders
        # Retrieve additional orders while there is a next page of results
        while response.NextToken:
            logger.info(f"Fetching additional orders for {response.NextToken}")
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
