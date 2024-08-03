from typing import List
from crud.common.standardize import *
from core.db import MongoDBDataManager


class SummaryDataManager(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_amazon_data = "amazon_data"
        self.db_carrier = "carrier"
        self.collection_orders = "orders"
        self.collection_catalog = "catalog"
        self.collection_shipments = "shipments"


class PickPackDataManager(SummaryDataManager):

    def __init__(self):
        super().__init__()

    def get_orders_by_id(self, ids: List[str]):
        orders = []
        mdb_orders_coll = self.db_client[self.db_amazon_data][self.collection_orders]
        o = list(mdb_orders_coll.find({"_id": {"$in": ids}}))
        orders.extend(o)
        return orders

    def get_catalog_by_id(self, ids: List[str]):
        catalog = []
        mdb_catalog_coll = self.db_client[self.db_amazon_data][self.collection_catalog]
        c = list(mdb_catalog_coll.find({"_id": {"$in": ids}}))
        catalog.extend(c)
        return catalog

    def get_shipments_by_id(self, ids: List[str]):
        shipments_coll = self.db_client[self.db_carrier][self.collection_shipments]
        shipments = list(shipments_coll.find({"_id": {"$in": ids}}))
        return shipments


class ShipmentReportManager(SummaryDataManager):

    def __init__(self):
        super().__init__()

    def export_shipment_report_to_excel(self, from_date: str, to_date: str) -> bytes:
        """
        TODO:Export shipment report to Excel file.
        :param shipment_ids:  List of shipment ids.
        :return:  Excel file in bytes.
        """
        pass
