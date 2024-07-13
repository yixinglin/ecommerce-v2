import time
from typing import List, Union, Tuple
from utils.stringutils import jsonpath, remove_duplicates
from core.db import MongoDBDataManager, ShipmentMongoDBDataManager
from core.exceptions import ShipmentExistsException
from core.log import logger
from models.shipment import StandardShipment, Address, Parcel, Event
import utils.utilpdf as utilpdf
from .shipment import GlsShipmentApi, GlsApiKey
import utils.time as time_utils

"""
Database Structure:
carrier
    - shipments
    - invoices
    
@ Zugestellt:  20103703352, DELIVERED
Daten übermittelt: 20103722357, PREADVICE
Zugestellt im PaketShop: 20103722721, DELIVEREDPS
In Abholung: 20103790165, INPICKUP
Unterwegs: 	20103790166, INTRANSIT
@ Beendete Pakethistorie: 20103299849, FINAL
@ Storniert, 20103473979, CANCELED

"""


class GlsShipmentMongoDBManager(ShipmentMongoDBDataManager):
    """
    This class is responsible for managing the shipment data in the MongoDB database.
    """

    def __init__(self, key_index):
        super().__init__()
        self.carrier_name = "gls"
        self.db_name = "carrier"
        self.collection_name = "shipments"
        if key_index is not None:
            key = GlsApiKey.from_json(index=key_index)
            self.api = GlsShipmentApi(api_key=key)
            logger.info(f"Using {self.carrier_name}-API with alias [{key.alias}]")

    def save_shipment(self, shipment: StandardShipment) -> str:
        """
        Fetch the shipment data from the API and save it to the database.
        If the shipment data is already in the database,
        raise a ShipmentExistsException if the shipment already exists.
        :param shipment:  StandardShipment object
        :return: The shipment id of the saved shipment.
        """
        # Check if the shipment data is already in the database. If not, insert it.
        _id = shipment.shipment_id()
        shipmentDB = self.find_shipment_by_id(_id)
        if shipmentDB:
            # Shipment already exists in database
            raise ShipmentExistsException(f"Shipment with id [{_id}] already exists in database.")

        # Generate shipment via API
        resp_data = self.api.generate_label(shipment)
        # write trackId and parcelNumber to the shipment object
        created_at = time_utils.now()
        parcelNumbers = jsonpath(resp_data, '$.parcels[*].parcelNumber')
        trackIds = jsonpath(resp_data, '$.parcels[*].trackId')
        parcelLocations = jsonpath(resp_data, '$.parcels[*].location')
        shipment.location = resp_data['location']
        shipment.carrier = self.carrier_name
        shipment.createdAt = created_at
        shipment.label = resp_data['labels'][0]

        if not isinstance(parcelNumbers, list):
            parcelNumbers = [parcelNumbers]
            trackIds = [trackIds]
            parcelLocations = [parcelLocations]

        for i in range(len(parcelNumbers)):
            shipment.parcels[i].parcelNumber = parcelNumbers[i]
            shipment.parcels[i].trackNumber = trackIds[i]
            shipment.parcels[i].locationUrl = parcelLocations[i]

        # Save shipment data to database
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]

        document = {
            "_id": _id,
            "details": shipment.dict(),
            "raw_resp": resp_data,
            "alias": self.api.api_key.alias
        }

        result = mdb_shipments_collection.insert_one(document)
        return result.inserted_id

    def save_shipments(self, shipments: List[StandardShipment]) -> Tuple[List[str], List[str]]:
        """
        Save multiple shipments to the database.
        :param shipments:  List of StandardShipment objects
        :return: List of shipment ids of the saved shipments. The first list contains the new shipment ids,
        and the second list contains the existing shipment ids.
        """
        new_ids = []
        exist_ids = []
        fail_ids = []
        _id = ""
        # Validate all shipments before saving
        self.api.validate_shipments(shipments)
        for shipment in shipments:
            try:
                _id = shipment.shipment_id()
                _id = self.save_shipment(shipment)
                logger.info(f"Saved shipment with id [{_id}]")
                new_ids.append(_id)
                time.sleep(0.2)
            except ShipmentExistsException as e:
                logger.warning(str(e))
                exist_ids.append(_id)
            # Handle other exceptions to avoid crashing the program
            except Exception as e:
                logger.error(f"Error while creating shipment {_id}: {str(e)}")
                fail_ids.append(_id)
        return new_ids, exist_ids


    def is_shipment_cycle_completed(self, shipment: StandardShipment) -> bool:
        """
        Check if the shipment is completed by checking if all the parcels are delivered.
        :param shipment:  StandardShipment object
        :return: True if the shipment is completed, False otherwise.
        """
        # Check if all parcels are delivered or canceled or final
        for parcel in shipment.parcels:
            if parcel.status != "DELIVERED" and parcel.status != "CANCELED"\
                    and parcel.status != "FINAL":
                return False
        # All parcels are delivered or canceled or final
        return True


    def save_tracking_info(self, ids: List[str]):
        """
        Save the tracking information for the shipment with the given reference numbers.
        :param ids:  List of reference numbers
        :return:
        """
        shipments = self.find_shipments_by_ids(ids)
        # TODO: Filter out shipments that are delivered or cancelled
        shipments = [s for s in shipments if not self.is_shipment_cycle_completed(s)]
        if not shipments:
            logger.info(f"No shipments to track.")
            return

        # Get all parcels from the shipments
        parcels = []
        # parcel_to_shipment = {}
        for shipment in shipments:
            parcels.extend(shipment.parcels)
        trackId_to_parcel = {parcel.parcelNumber: parcel for parcel in parcels}
        parcelNumbers = list(trackId_to_parcel.keys())
        # Get tracking information from API
        resp = self.api.fetch_tracking_info(parcelNumbers)
        dic_events = {}
        for parcel_data in resp['parcels']:
            status = parcel_data['status']
            parcelNumber = parcel_data['trackid']
            events = [self.to_standerd_event(e) for e in parcel_data['events']]
            dic_events[parcelNumber] = dict(status=status, events=events)

        for parcel_number, parcel in trackId_to_parcel.items():
            parcel.status = dic_events[parcel_number]["status"]
            parcel.events = dic_events[parcel_number]["events"]
        # Update tracking information in database
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        for shipment in shipments:
            _id = shipment.shipment_id()
            mdb_shipments_collection.update_one(
                {"_id": _id},
                {"$set": {"details.parcels": [p.dict() for p in shipment.parcels]}}
            )

    def delete_shipment(self, id: str):
        # Delete shipment data from database by reference number
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        result = mdb_shipments_collection.delete_one({"_id": id, "carrier": self.carrier_name})
        return result.deleted_count

    def to_standard_shipment(self, shipment_data: dict) -> StandardShipment:
        """
        Convert the shipment data from the database to a StandardShipment object.
        :param shipment_data: Shipment data from the database
        :return: StandardShipment object

        Details就是StandardShipment的属性，所以这里可以直接用Details，不需要再转换一次
        """
        standard_shipment = StandardShipment.parse_obj(shipment_data['details'])
        return standard_shipment

    def to_standerd_event(self, event_data: dict) -> Event:
        event = Event(
            timestamp=jsonpath(event_data, '$.timestamp'),
            location=jsonpath(event_data, '$.location'),
            description=jsonpath(event_data, '$.description'),
            country=jsonpath(event_data, '$.country')
        )
        return event

    def find_shipments(self, filter_: dict) -> List[StandardShipment]:
        """
        Find shipment data in database by filter.
        @Note: This function is a low-level function. Do not modify without proper review.
        :param filter_:
        :return:
        """
        mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        result = mdb_shipments_collection.find(filter=filter_)
        result = list(result)
        return list(map(lambda x: self.to_standard_shipment(x), result))

    def find_shipments_by_ids(self, ids: List[str]) -> List[StandardShipment]:
        """
        Find shipment data in database by reference numbers.
        @Note: This function is a low-level function. Do not modify without proper review.
        :param ids:
        :return:
        """
        filter_ = {"_id": {"$in": ids}, "details.carrier": self.carrier_name}
        result = self.find_shipments(filter_=filter_)
        # Sort the shipment by ids
        map_shipments = {s.shipment_id(): s for s in result}
        result = [map_shipments[id] for id in ids if id in map_shipments.keys()]
        return result

    def find_shipment_by_id(self, id: str) -> Union[StandardShipment, None]:
        """
        Find shipment data in database by reference number.
        @Note: This function is a low-level function. Do not modify without proper review.
        :param id:
        :return:
        """
        result = self.find_shipments_by_ids([id])
        if result:
            return result[0]
        else:
            return None

    def get_incomplete_shipments(self, days_ago: int = 7) -> List[StandardShipment]:
        """
        Get all incomplete shipments in the last 7 days from the database.
        :return:
        """
        filter_ = {"details.parcels.status":
                       {"$nin": ["DELIVERED", "CANCELED", "FINAL"]},
                   "details.createdAt": {"$gte": time_utils.days_ago(days_ago)},
                   "alias": self.api.api_key.alias
                   }
        shipments = self.find_shipments(filter_=filter_)
        return shipments

    def get_bulk_shipments_labels(self, references: List[str]) -> bytes:
        """
        Get the bulk shipment labels by reference numbers.
        :param references:  List of reference numbers
        :return: PDF data
        """
        references = remove_duplicates(references)
        logger.info(f"Getting bulk shipment labels for references: {references}")
        bulkPdfDataList: List[bytes] = []
        shipments = self.find_shipments_by_ids(references)
        for shipment in shipments:
            if not shipment:
                raise RuntimeError(f"Shipment with reference number [{shipment.shipment_id()}] not found in database.")
            if shipment.carrier != self.carrier_name:
                raise RuntimeError(f"Shipment with reference number [{shipment.shipment_id()}] is not from {self.carrier_name}.")
            # shipment_details = StandardShipment.parse_obj(shipment['details'])
            pdfData: bytes = utilpdf.str_to_pdf(shipment.label)
            pdfData = self.__decorate_shipment(shipment, pdfData)
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
        content = f"Von: {self.api.api_key.alias}\n"
        content += shipment.parcels[0].content
        result = utilpdf.add_watermark(pdfData, content, font_size=7, position=utilpdf.GLS_TEXT_POS)
        return result
