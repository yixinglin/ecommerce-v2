from typing import List
from utils.stringutils import jsonpath
from core.db import MongoDBDataManager
from core.exceptions import ShipmentExistsException
from core.log import logger
from models.shipment import StandardShipment
import utils.utilpdf as utilpdf
from .shipment import GlsShipmentApi, GlsApiKey
import utils.time as time_utils

"""
Database Structure:
carrier
    - shipments
    - invoices
"""


class GlsShipmentMongoDBManager(MongoDBDataManager):
    """
    This class is responsible for managing the shipment data in the MongoDB database.
    """

    def __init__(self, db_host, db_port, key_index):
        super().__init__(db_host, db_port)
        key = GlsApiKey.from_json(index=key_index)
        self.api = GlsShipmentApi(api_key=key)
        self.db_name = "carrier"
        self.collection_name = "shipments"
        self.carrier_name = "gls"
        logger.info(f"Using {self.carrier_name}-API with alias [{key.alias}]")

    def get_shipment_id(self, shipment: StandardShipment) -> str:
        """
        Generate a unique shipment id based on the shipment details.
        :param shipment:  StandardShipment object
        :return:  A unique shipment id
        """
        return ";".join(shipment.references)

    def save_shipment(self, shipment: StandardShipment) -> str:
        """
        Fetch the shipment data from the API and save it to the database.
        If the shipment data is already in the database,
        raise a ShipmentExistsException if the shipment already exists.
        :param shipment:  StandardShipment object
        :return: The shipment id of the saved shipment.
        """
        # Check if the shipment data is already in the database. If not, insert it.
        _id = self.get_shipment_id(shipment)
        shipmentDB = self.find_shipment(_id)
        if shipmentDB:
            # Shipment already exists in database
            raise ShipmentExistsException(f"Shipment with id [{_id}] already exists in database.")

        # Generate shipment via API
        resp_data = self.api.generate_label(shipment)
        # write trackId and parcelNumber to the shipment object
        parcelNumbers = jsonpath(resp_data, '$.parcels[*].parcelNumber')
        trackIds = jsonpath(resp_data, '$.parcels[*].trackId')
        shipment.location = resp_data['location']

        for i in range(len(parcelNumbers)):
            shipment.parcels[i].parcelNumber = parcelNumbers[i]
            shipment.parcels[i].trackNumber = trackIds[i]

        # Save shipment data to database
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        created_at = time_utils.now()
        document = {
            "_id": _id,
            "carrier": self.carrier_name,
            "createdAt": created_at,
            "details": shipment.dict(),
            "data": resp_data,
            "alias": self.api.api_key.alias
        }

        result = mdb_shipments_collection.insert_one(document)
        return result.inserted_id

    def delete_shipment(self, id: str):
        # Delete shipment data from database by reference number
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        result = mdb_shipments_collection.delete_one({"_id": id, "carrier": self.carrier_name})
        return result.deleted_count

    def find_shipment(self, id: str):
        # Find shipment data in database by reference number
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        result = mdb_shipments_collection.find_one({"_id": id, "carrier": self.carrier_name})
        return result

    def find_shipments_by_ids(self, ids: List[str]):
        # Find shipment data in database by reference number
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        result = mdb_shipments_collection.find({"_id": {"$in": ids}, "carrier": self.carrier_name})
        return list(result)

    def get_bulk_shipments_labels(self, references: List[str]) -> bytes:
        """
        Get the bulk shipment labels by reference numbers.
        :param references:  List of reference numbers
        :return: PDF data
        """
        logger.info(f"Getting bulk shipment labels for references: {references}")
        bulkPdfDataList: List[bytes] = []
        for ref in references:
            shipment = self.find_shipment(id=ref)
            if not shipment:
                raise RuntimeError(f"Shipment with reference number [{ref}] not found in database.")
            if shipment['carrier'] != self.carrier_name:
                raise RuntimeError(f"Shipment with reference number [{ref}] is not from {self.carrier_name}.")
            shipment_details = StandardShipment.parse_obj(shipment['details'])
            pdfData: bytes = utilpdf.str_to_pdf(shipment['data']['labels'][0])
            pdfData = self.__decorate_shipment(shipment_details, pdfData)
            bulkPdfDataList.append(pdfData)
        mergedPdfData = utilpdf.concat_pdfs(bulkPdfDataList)
        return mergedPdfData

    def __decorate_shipment(self, shipment: StandardShipment, pdfData: bytes) -> bytes:
        """
        Decorate the shipment PDF with additional information such as the shipment details,
        :param shipment: StandardShipment object
        :param pdfData: Shipment PDF data as bytes
        :return:
        """
        content = shipment.parcels[0].content
        result = utilpdf.add_watermark(pdfData, content, font_size=7, position=utilpdf.GLS_TEXT_POS)
        return result

    # def get_pick_slips_by_references(self, references: List[str]) -> List[dict]:
    #     """
    #     Get the pick slips by reference numbers.
    #     :param references:
    #     :return:
    #     """
    #     shipments = self.find_shipments_by_ids(references)
    #     pass


