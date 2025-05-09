from typing import List

from core.log import logger
from models.warehouse import Quant, PutawayRule
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
            if quant['data']['warehouse_id'] == False:
                continue
            q = self.to_standard_quant(quant)
            quants.append(q)
        location_ids = [int(q.locationId) for q in quants]
        location_data = self.mdb_location.query_storage_location_by_ids(location_ids)
        barcode_map = {loc['_id']: loc['data']['barcode'] for loc in location_data }
        for quant in quants:
            quant.locationCode = barcode_map.get(int(quant.locationId), "")

        ans = dict(
            alias=self.api.get_alias(),
            size=len(quants),
            quants=quants,
        )
        return ans

    def request_quant_by_id(self, quant_id, inv_quantity):
        ans = self.api.request_quant_by_id(quant_id, inv_quantity)
        if ans:
            logger.info(f"Request quant {quant_id} success")
        else:
            logger.error(f"Request quant {quant_id} failed")
        return ans

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

    def query_putaway_rules_by_putaway_rule_ids(self, putaway_rule_ids, offset, limit):
        # Query putaway rules by location ids from DB
        filter_ = {"alias": self.api.get_alias(),
                   "data.id": {"$in": putaway_rule_ids}}
        data = self.mdb_putaway_rule.query_putaway_rules(offset=offset, limit=limit,
                                                         filter=filter_)

        # Convert to standard putaway rule
        putaway_rules: List[PutawayRule] = []
        for putaway_rule in data:
            rule = self.to_standard_putaway_rule(putaway_rule)
            putaway_rules.append(rule)

        location_in_ids = [int(rule.locationInId) for rule in putaway_rules]
        location_out_ids = [int(rule.locationOutId) for rule in putaway_rules]
        location_ids = list(set(location_in_ids + location_out_ids))
        location_data = self.mdb_location.query_storage_location_by_ids(location_ids)
        barcode_map = {loc['_id']: loc['data']['barcode'] for loc in location_data }
        for rule in putaway_rules:
            rule.locationInCode = barcode_map.get(int(rule.locationInId), "")
            rule.locationOutCode = barcode_map.get(int(rule.locationOutId), "")

        ans = dict(
            alias=self.api.get_alias(),
            size=len(putaway_rules),
            putaway_rules=putaway_rules,
        )
        return ans

    def move_quants_by_putaway_rules(self, putaway_rule_id):
        # TODO: Move quant by putaway rule
        raise NotImplementedError()

    def create_putaway_rule(self, product_id:int, location_out_id:int, location_in_id:int=8):
        # Create putaway rule in Odoo
        rule_id = self.api.create_putaway_rule(product_id=product_id,
                                     location_out_id=location_out_id,
                                     location_in_id=location_in_id)
        if rule_id:
            logger.info(f"Create putaway rule {rule_id} success")
            self.save_putaway_rule(rule_id)
        else:
            logger.error(f"Create putaway rule {rule_id} failed")
        return rule_id

    def update_putaway_rule(self, rule_id:int, location_out_id:int, location_in_id:int=8):
        # Update putaway rule in Odoo
        success = self.api.update_putaway_rule(rule_id=rule_id,
                                     location_out_id=location_out_id,
                                     location_in_id=location_in_id)
        if success:
            logger.info(f"Update putaway rule {rule_id} success")
            self.save_putaway_rule(rule_id)
        else:
            logger.error(f"Update putaway rule {rule_id} failed")
        return success

