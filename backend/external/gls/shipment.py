"""
Generate various type of labels for GLS parcels

This module provides a class for generating various type of labels for GLS parcels.

Example usage:
Generate a label via API call, then add some strings on it for customization.
"""
import json
from copy import deepcopy
from typing import List
import requests
from core.config import settings
from core.log import logger
from models.shipment import StandardShipment
from utils.address import adjust_name_fields
from utils.auth import basic_auth
from .base import GLSRequestBody, GLS_HEADERS_EU, GlsApiKey

MAX_NAME_LENGTH = 37


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
            = adjust_name_fields(address.name1, address.name2, address.name3, MAX_NAME_LENGTH)
        if not self.__check_name_length((address.name1, address.name2, address.name3)):
            raise RuntimeError(f"Name length exceeds maximum limit of {MAX_NAME_LENGTH} characters {address}")
        return shipment

    def validate_shipments(self, shipments: List[StandardShipment]):
        ans = []
        for shipment in shipments:
            ship = deepcopy(shipment)
            self.__preprocess(ship)
            ans.append(ship)
        return ans

    def create_label(self, shipment: StandardShipment) -> dict:
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

    def __check_name_length(self, names: List[str]):
        for name in names:
            if len(name) > MAX_NAME_LENGTH:
                return False
        return True

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


