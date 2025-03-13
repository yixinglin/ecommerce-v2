import json
import os
from datetime import datetime
from typing import Union

from sp_api.base import Marketplaces
from sp_api.api import Sellers
from core.config2 import settings
from pydantic import BaseModel, Field

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
                                 settings.api_keys.amazon_access_key)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = cls(**data["auth"][index])
        return k

    def get_marketplace_participation(self, marketplace: Marketplaces):
        return Sellers(credentials=self.__dict__, marketplace=marketplace).get_marketplace_participation().payload

class AmazonAddress(BaseModel):
    CompanyName: Union[str, None] = Field(default=None, description="CompanyName")
    Name: Union[str, None] = Field(default=None, description="Name")
    AddressLine1: Union[str, None] = Field(default=None, description="AddressLine1: street")
    AddressLine2: Union[str, None] = Field(default=None, description="AddressLine2: c/o")
    City: Union[str, None] = Field(default=None, description="City")
    Country: Union[str, None] = Field(default=None, description="Country")
    CountryCode: Union[str, None] = Field(default=None, description="CountryCode")
    StateOrRegion: Union[str, None] = Field(default=None, description="StateOrRegion")
    PostalCode: Union[str, None] = Field(default=None, description="PostalCode")
    Phone: Union[str, None] = Field(default=None, description="Phone")



