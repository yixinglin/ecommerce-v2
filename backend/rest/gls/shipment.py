"""
Generate various type of labels for GLS parcels

This module provides a class for generating various type of labels for GLS parcels.

Example usage:
Generate a label via API call, then add some strings on it for customization.
"""
import json
import os
from typing import List
import requests
from pydantic import BaseModel
from core.config import settings
from core.log import logger
from models.shipment import StandardShipment
from utils.auth import basic_auth
from .base import GLSRequestBody, GLS_HEADERS_EU

MAX_NAME_LENGTH = 37


class GlsApiKey(BaseModel):
    url: str
    alias: str
    username: str
    password: str
    shipperId: str

    @classmethod
    def from_json(cls, index):
        """
        Load API key from JSON file
        :param keyName: Name of the API key in the JSON file
        :return:
        """
        file_path = os.path.join('conf', 'apikeys',
                                 settings.GLS_ACCESS_KEY)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = cls(**data["keys"][index])
        return k


class GlsShipmentApi:

    def __init__(self, api_key: GlsApiKey):
        self.api_key = api_key
        self.auth = basic_auth(api_key.username, api_key.password)
        self.headers: dict = GLS_HEADERS_EU

    def __preprocess(self, shipment: StandardShipment):
        """
        Input data preprocessing before generating labels
        :param shipment:
        :return:
        """
        # Basic authentication and shipperId
        self.headers['Authorization'] = self.auth
        # Validate length of the given names
        address = shipment.consignee
        address.name1, address.name2, address.name3 \
            = self.adjustNameFields(address.name1, address.name2, address.name3)
        if not self.__checkNameLength((address.name1, address.name2, address.name3)):
            raise RuntimeError(f"Name length exceeds maximum limit of {MAX_NAME_LENGTH} characters")
        return shipment

    def generate_label(self, shipment: StandardShipment) -> dict:
        """
        Generate a label for a given shipment
        :param shipment:
        :return:
        """
        # Preprocess input data to meet GLS API requirements
        logger.info(f"Generating label for shipment {shipment.dict()}")
        shipment = self.__preprocess(shipment)
        # Get a request body for the label generation
        body = GLSRequestBody.instance(shipment=shipment)
        body.shipperId = self.api_key.shipperId
        shipment_url = f"{self.api_key.url}/shipments"
        # Request to GLS API to generate label
        logger.info(f"[API] Request URL: {shipment_url}, body: {body.dict()}")
        resp = requests.post(shipment_url, headers=self.headers, json=body.dict())
        if resp.status_code == 201:
            logger.info(f"GLS-Label generated successfully")
            data = json.loads(resp.text)
        else:
            raise RuntimeError(f"Failed to generate GLS-label "
                               f"for request {body.dict()}: {resp.text}")
        return data

    def __checkNameLength(self, names: List[str]):
        for name in names:
            if len(name) > MAX_NAME_LENGTH:
                return False
        return True

    def adjustNameFields(self, name1, name2, name3):
        tmp = ""
        if len(name1) >= MAX_NAME_LENGTH:
            tmp = name1[MAX_NAME_LENGTH:]
            name1 = name1[:MAX_NAME_LENGTH]
            if len(name3) > 0:
                name2 = tmp + " || " + name2
            else:
                name3 = name2
                name2 = tmp
        if len(name2) >= MAX_NAME_LENGTH:
            tmp = name2[MAX_NAME_LENGTH:]
            name2 = name2[:MAX_NAME_LENGTH]
            if len(name3) > 0:
                name3 = tmp + " || " + name3
            else:
                name3 = tmp
        return [name1, name2, name3]


