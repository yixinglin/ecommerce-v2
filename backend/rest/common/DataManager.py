import re
from sp_api.base import Marketplaces
from core.db import MongoDBDataManager
from core.log import logger
from rest.amazon.DataManager import AmazonOrderMongoDBManager, AmazonCatalogManager
from rest.gls.DataManager import GlsShipmentMongoDBManager
from schemas.basic import ExternalService


class CommonMongoDBManager(MongoDBDataManager):
    """
    This class is only used to query data from MongoDB.
    """
    def __init__(self):
        super().__init__()
        logger.info("CommonMongoDBManager init")

    def __enter__(self):
        super().__enter__()
        return self


    def recognize_by_reference_format(self, reference: str) -> ExternalService:
        """
        Recognize sales channel by reference format
        """
        if reference is None or reference == "":
            raise RuntimeError("Empty reference is not allowed")

        if re.match(r"^[0-9]{3}-[0-9]{7}-[0-9]{7}$", reference):
            return ExternalService.Amazon
        else:
            raise RuntimeError(f"Invalid reference format: {reference}")






