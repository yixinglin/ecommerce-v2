"""
Generate various type of labels for GLS parcels

This module provides a class for generating various type of labels for GLS parcels.

Example usage:
Generate a label via API call, then add some strings on it for customization.
"""
import json
import os
from copy import deepcopy
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
            raise RuntimeError(f"Name length exceeds maximum limit of {MAX_NAME_LENGTH} characters {address}")
        return shipment

    def validate_shipments(self, shipments: List[StandardShipment]):
        ans = []
        for shipment in shipments:
            ship = deepcopy(shipment)
            self.__preprocess(ship)
            ans.append(ship)
        return ans

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
        if settings.DEBUG:
            body.clearServices() # Avoid sending unnecessary services to GLS API in debug mode
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

    # def adjustNameFields(self, name1, name2, name3):
    #     tmp = ""
    #     if len(name1) >= MAX_NAME_LENGTH:
    #         tmp = name1[MAX_NAME_LENGTH:]
    #         name1 = name1[:MAX_NAME_LENGTH]
    #         if len(name3) > 0:
    #             name2 = tmp + " || " + name2
    #         else:
    #             name3 = name2
    #             name2 = tmp
    #     if len(name2) >= MAX_NAME_LENGTH:
    #         tmp = name2[MAX_NAME_LENGTH:]
    #         name2 = name2[:MAX_NAME_LENGTH]
    #         if len(name3) > 0:
    #             name3 = tmp + " || " + name3
    #         else:
    #             name3 = tmp
    #     return [name1, name2, name3]


    def adjustNameFields(self, name1, name2, name3):
        tmp = ""
        if len(name1) >= MAX_NAME_LENGTH:
            tmp = name1[MAX_NAME_LENGTH:]
            name1 = name1[:MAX_NAME_LENGTH]
            if len(name3) > 0 or len(name2) > MAX_NAME_LENGTH:
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


    # def adjustNameFields(self, name1, name2, name3):
    #     MAX_LENGTH = 37
    #     names = [name1, name2, name3]
    #
    #     for i in range(len(names)):
    #         if len(names[i]) > MAX_LENGTH:
    #             excess_part = names[i][MAX_LENGTH:]
    #             names[i] = names[i][:MAX_LENGTH].rstrip()
    #             if excess_part:
    #                 if i < len(names) - 1:
    #                     if names[i + 1]:
    #                         names[i + 1] = excess_part.lstrip() + ' | ' + names[i + 1].lstrip()
    #                     else:
    #                         names[i + 1] = excess_part.lstrip()
    #     return names[0], names[1], names[2]

    def fetch_tracking_info(self, trackId: List[str]) -> dict:
        # https://api.gls-group.eu/public/v1/tracking/references
        joined_track_ids = ",".join(trackId)
        tracking_url = f"{self.api_key.url}/tracking/references/{joined_track_ids}"
        logger.info(f"[API] Request URL: {tracking_url}")
        self.headers['Authorization'] = self.auth
        resp = requests.get(tracking_url, headers=self.headers)
        if resp.status_code == 200:
            data = json.loads(resp.text)
        else:
            raise RuntimeError(f"Failed to fetch tracking info for trackId {trackId}: {resp.text}")
        return data


