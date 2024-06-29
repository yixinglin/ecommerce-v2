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
    def __init__(self, db_host, db_port):
        super().__init__(db_host, db_port)
        logger.info("CommonMongoDBManager init")
        self.glsShipmentDataManager = GlsShipmentMongoDBManager(db_host, db_port, None)
        self.amazonDataManager = AmazonOrderMongoDBManager(db_host, db_port, None, Marketplaces.DE)
        self.amazonCatalogManager = AmazonCatalogManager(db_host, db_port, None, Marketplaces.DE, )

        self.registered_managers = [self.glsShipmentDataManager,
                                    self.amazonDataManager, self.amazonCatalogManager]


    def __enter__(self):
        super().__enter__()
        for manager in self.registered_managers:
            manager.db_client = self.db_client
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






