import json
import os
from datetime import datetime
from sp_api.base import Marketplaces
from sp_api.api import Sellers
from core.config import settings
from pydantic import BaseModel

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'

MARKETPLACES_MAP = {p.name: p for p in Marketplaces}

def now():
    return datetime.now().strftime(DATETIME_PATTERN)


def today():
    return datetime.now().date()


# This class represents the Amazon Sp API keys and provides methods to fetch orders and order items
class AmazonSpAPIKey(BaseModel):

    account_id: str
    refresh_token: str
    lwa_app_id: str
    lwa_client_secret: str
    aws_access_key: str
    aws_secret_key: str
    role_arn: str

    def get_account_id(self):
        return self.account_id

    @staticmethod
    def name_to_marketplace(name: str):
        """
        Converts the marketplace name to the Marketplaces enum
        :param name:  Name of the marketplace, e.g. 'US', 'UK', 'DE', 'JP'
        :return: Marketplaces enum
        """
        if name in MARKETPLACES_MAP.keys():
            marketplace = MARKETPLACES_MAP[name]
        else:
            raise RuntimeError(f"Marketplace [{name}] not supported")
        return marketplace

    @classmethod
    def from_json(cls, index):
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
        k = cls(**data["auth"][index])
        # k.__dict__.update(**data["auth"][index])
        return k

    def get_marketplace_participation(self, marketplace: Marketplaces):
        return Sellers(credentials=self.__dict__, marketplace=marketplace).get_marketplace_participation().payload
