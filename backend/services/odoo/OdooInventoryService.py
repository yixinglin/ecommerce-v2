from core.log import logger
from models.warehouse import Quant
from .base import OdooInventoryServiceBase, save_record

class OdooInventoryService(OdooInventoryServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

    def save_all_internal_locations(self):
        fetch_object_ids = self.api.fetch_internal_location_ids
        fetch_write_date = self.api.fetch_location_write_date
        query_object_by_id = self.mdb_location.query_storage_location_by_id
        save_object = self.save_location
        object_name = 'stock.location'
        save_record(fetch_object_ids, fetch_write_date,
                         query_object_by_id, object_name, save_object)

    def save_all_quants(self):
        fetch_object_ids = self.api.fetch_quant_ids
        fetch_write_date = self.api.fetch_quant_write_date
        query_object_by_id = self.mdb_quant.query_quant_by_id
        save_object = self.save_quant
        object_name = 'stock.quant'
        save_record(fetch_object_ids, fetch_write_date,
                         query_object_by_id, object_name, save_object)

    def save_all_putaway_rules(self):
        fetch_object_ids = self.api.fetch_putaway_rule_ids
        fetch_write_date = self.api.fetch_putaway_rule_write_date
        query_object_by_id = self.mdb_putaway_rule.query_putaway_rule_by_id
        save_object = self.save_putaway_rule
        object_name = 'stock.putaway.rule'

        save_record(fetch_object_ids, fetch_write_date,
                         query_object_by_id, object_name, save_object)

    def query_all_quants(self, offset, limit):
        # Query all quants from DB
        filter_ = {"alias": self.api.get_alias()}
        data = self.mdb_quant.query_quants(offset=offset, limit=limit, filter=filter_)
        quants: Quant = []
        for quant in data:
            q = self.to_standard_quant(quant)
            quants.append(q)
        ans = dict(
            alias=self.api.get_alias(),
            size=len(quants),
            quants=quants,
        )
        return ans

    def query_quants_by_quant_ids(self, quant_ids, offset, limit):
        # Query quants by location ids from DB
        filter_ = {"alias": self.api.get_alias(),
                   "data.id": {"$in": quant_ids}}
        data = self.mdb_quant.query_quants(offset=offset, limit=limit, filter=filter_)
        quants: Quant = []
        for quant in data:
            q = self.to_standard_quant(quant)
            quants.append(q)
        ans = dict(
            alias=self.api.get_alias(),
            size=len(quants),
            quants=quants,
        )
        return ans

    # def query_quants_by_product_id(self, product_id, offset, limit):
    #     # Query quants by product id from DB
    #     filter_ = {"alias": self.api.get_alias(),
    #                "data.product_id": product_id}
    #     data = self.mdb_quant.query_quants(offset=offset, limit=limit, filter=filter_)
    #     quants: Quant = []
    #     for quant in data:
    #         q = self.to_standard_quant(quant)
    #         quants.append(q)
    #     ans = dict(
    #         alias=self.api.get_alias(),
    #         size=len(quants),
    #         quants=quants,
    #     )
    #     return ans


    def query_all_locations(self, offset, limit):
        # Query all locations from DB
        filter_ = {"alias": self.api.get_alias(), "data.active": True}
        data = self.mdb_location.query_storage_locations(offset=offset, limit=limit,
                                                         filter=filter_)
        locations = []
        for location in data:
            locations.append(dict(
                fetchedAt=location.get('fetchedAt', ""),
                location=location.get('data', ""),))
        ans = dict(
            alias=self.api.get_alias(),
            size=len(locations),
            locations=locations,
        )
        return ans

    def query_all_putaway_rules(self, offset, limit):
        # Query all putaway rules from DB
        filter_ = {"alias": self.api.get_alias(), "data.active": True}
        data = self.mdb_putaway_rule.query_putaway_rules(offset=offset, limit=limit,
                                                         filter=filter_)
        putaway_rules = []
        for putaway_rule in data:
            putaway_rules.append(dict(
                fetchedAt=putaway_rule.get('fetchedAt', ""),
                putaway_rule=putaway_rule.get('data', ""),))
        ans = dict(
            alias=self.api.get_alias(),
            size=len(putaway_rules),
            putaway_rules=putaway_rules,
        )
        return ans

    def move_quants_by_putaway_rules(self, putaway_rule_id):
        # TODO: Move quant by putaway rule
        raise NotImplementedError()

