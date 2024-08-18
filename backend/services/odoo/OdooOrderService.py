from core.log import logger
from .base import save_record
from .base import (OdooProductServiceBase, OdooContactServiceBase)



class OdooProductService(OdooProductServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

    def save_all_product_templates(self):
        fetch_object_ids = self.api.fetch_product_template_ids
        fetch_write_date = self.api.fetch_product_template_write_date
        query_object_by_id = self.mdb_product_templ.query_product_template_by_id
        save_object = self.save_product_template
        object_name = 'product.template'
        save_record(fetch_object_ids, fetch_write_date,
                    query_object_by_id, object_name, save_object)

    def save_all_products(self):
        fetch_object_ids = self.api.fetch_product_ids
        fetch_write_date = self.api.fetch_product_write_date
        query_object_by_id = self.mdb_product.query_product_by_id
        save_object = self.save_product
        object_name = 'product.product'
        save_record(fetch_object_ids, fetch_write_date,
                    query_object_by_id, object_name, save_object)


class OdooContactService(OdooContactServiceBase):

    def __init__(self, key_index, *args, **kwargs):
        super().__init__(key_index, *args, **kwargs)

    def save_all_contacts(self):
        fetch_object_ids = self.api.fetch_contact_ids
        fetch_write_date = self.api.fetch_contact_write_date
        query_object_by_id = self.mdb_contact.query_contact_by_id
        save_object = self.save_contact
        object_name = 'res.partner'
        save_record(fetch_object_ids, fetch_write_date,
                    query_object_by_id, object_name, save_object)

