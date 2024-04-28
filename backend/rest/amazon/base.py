import json
import os
from datetime import datetime
from typing import Tuple
from sp_api.base import Marketplaces
from sp_api.api import Sellers
from core.config import settings
from pydantic import BaseModel

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'


def now():
    return datetime.now().strftime(DATETIME_PATTERN)


def today():
    return datetime.now().date()


# This class represents the Amazon Sp API keys and provides methods to fetch orders and order items
class AmazonSpAPIKey(BaseModel):
    def __init__(self):
        self.account_id: str
        self.refresh_token: str
        self.lwa_app_id: str
        self.lwa_client_secret: str
        self.aws_access_key: str
        self.aws_secret_key: str
        self.role_arn: str

    def get_account_id(self):
        return self.account_id

    @classmethod
    def from_json(cls, index=0):
        """
        Loads the API keys from the JSON file
        :param index: Index of the API key to load (default is 0)
        :return:
        """
        # Load the API keys from the JSON file
        file_path = os.path.join('conf', 'apikeys',
                                 settings.AMAZON_ACCESS_KEY)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = AmazonSpAPIKey()
        k.__dict__.update(data["auth"][index])
        return k

    def get_marketplace_participation(self):
        return Sellers(credentials=self.__dict__, marketplace=Marketplaces.DE).get_marketplace_participation().payload
