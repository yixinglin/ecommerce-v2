from typing import List

from core.db import ShipmentMongoDBDataManager
from models.shipment import StandardShipment, Event
from utils.stringutils import jsonpath


class GlsShipmentMongoDB(ShipmentMongoDBDataManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.carrier_name = "gls"
        self.db_name = "carrier"
        self.db_collection_name = "shipments"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_shipments(self, filter_: dict) -> List[StandardShipment]:
        """
        Find shipment data in database by filter.
        @Note: This function is a low-level function. Do not modify without proper review.
        :param filter_:
        :return:
        """
        # mdb_shipments_collection = self.db_client[self.db_name][self.collection_name]
        mdb_shipments_collection = self.get_db_collection()
        result = mdb_shipments_collection.find(filter=filter_)
        result = list(result)
        return list(map(lambda x: self.to_standard_shipment(x), result))

    def query_shipment_by_id(self, id: str) -> StandardShipment:
        """
        Find shipment data in database by reference number.
        @Note: This function is a low-level function. Do not modify without proper review.
        :param id:
        :return:
        """
        result = self.query_shipments_by_ids([id])
        if result:
            return result[0]
        else:
            return None

    def query_shipments_by_ids(self, ids: str) -> List[StandardShipment]:
        """
                Find shipment data in database by reference numbers.
                @Note: This function is a low-level function. Do not modify without proper review.
                :param ids:
                :return:
                """
        filter_ = {"_id": {"$in": ids}, "details.carrier": self.carrier_name}
        result = self.query_shipments(filter_=filter_)
        # Sort the shipment by ids
        map_shipments = {s.shipment_id(): s for s in result}
        result = [map_shipments[id] for id in ids if id in map_shipments.keys()]
        return result

    def save_shipment(self, document):
        mdb_shipments_collection = self.get_db_collection()
        return mdb_shipments_collection.insert_one(document)

    def delete_shipment(self, id: str, *args, **kwargs) -> bool:
        # Delete shipment data from database by reference number
        mdb_shipments_collection = self.get_db_collection()
        result = mdb_shipments_collection.delete_one({"_id": id, "details.carrier": self.carrier_name})
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