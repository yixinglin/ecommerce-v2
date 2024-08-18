from core.log import logger
from .base import OdooAPIKey, OdooAPIBase


class OdooContactAPI(OdooAPIBase):

    def __init__(self, api_key: OdooAPIKey):
        super().__init__(api_key)

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

