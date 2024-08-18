from core.log import logger
from services.odoo.base import OdooInventoryServiceBase, save_record

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

    def query_all_quant(self):
        # TODO: Query all quant from DB
        pass

    def move_quants_by_putaway_rules(self, putaway_rule_id):
        # TODO: Move quant by putaway rule
        pass
