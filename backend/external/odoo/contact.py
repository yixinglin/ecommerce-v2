from typing import List, Dict

from core.log import logger
from .base import OdooAPIKey, OdooAPIBase


class OdooContactAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_contact_ids(self, domain=[]):
        logger.info("Fetching contact ids")
        contact_ids = self.client.search('res.partner', [domain])
        return contact_ids

    def fetch_contacts_by_ids(self, ids):
        logger.info("Fetching contacts by ids")
        contacts = self.client.read('res.partner', [ids], {})
        return contacts

    def fetch_contact_write_date(self, ids):
        return self.fetch_write_date('res.partner', ids)

    def fetch_company_by_ref(self, ref) -> List[Dict]:
        logger.info("Fetching company by ref")
        domain = [('ref', '=', ref), ('is_company', '=', True)]
        return self.client.search_read('res.partner', [domain], {})

    def create_contact(self, contact_data) -> List[int]:
        logger.info("Creating contact")
        return self.client.create('res.partner', [contact_data])