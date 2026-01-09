import datetime
import os
import xmlrpc.client
from typing import List, Dict

from pydantic import BaseModel, Field
from core.config2 import settings
import json

DATETIME_PATTERN = '%Y-%m-%d %H:%M:%S'
DATE_PATTERN = '%Y-%m-%d'


def now():
    return datetime.now().strftime(DATETIME_PATTERN)


def today():
    return datetime.now().strftime(DATE_PATTERN)


class OdooAPIKey(BaseModel):
    alias: str
    db: str
    username: str
    password: str
    host: str

    @classmethod
    def from_json(cls, index):
        file_path = os.path.join('conf', 'apikeys',
                                 settings.api_keys.odoo_access_key)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = cls(**data['keys'][index])
        return k


class OdooClient(object):

    def __init__(self, api_key: OdooAPIKey):
        self.api_key = api_key
        self.db = api_key.db
        self.username = api_key.username
        self.password = api_key.password
        self.host = api_key.host
        self.uid = None
        self.models = None

    def login(self):
        print("Odoo API Login")
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.host))
        self.uid = common.authenticate(self.db, self.username, self.password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.host))
        return self

    def version(self):
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.host))
        return common.version()

    def execute_kw(self, model, method, *args, **kwargs):
        return self.models.execute_kw(self.db, self.uid, self.password,
                                      model, method, *args, **kwargs)

    def search_read(self, model, *args, **kwargs):
        return self.execute_kw(model,'search_read', *args, **kwargs)

    def search(self, model, *args, **kwargs):
        return self.execute_kw(model,'search', *args, **kwargs)

    def read(self, model, *args, **kwargs):
        return self.execute_kw(model,'read', *args, **kwargs)

    def create(self, model, *args, **kwargs):
        return self.execute_kw(model, 'create', *args, **kwargs)

    def write(self, model, *args, **kwargs):
        return self.execute_kw(model, 'write', *args, **kwargs)


class OdooAPIBase(object):

    def __init__(self, api_key: OdooAPIKey, login=True, *args, **kwargs):
        self.api_key = api_key
        self.client = OdooClient(self.api_key)
        if login:
            self.login()

    def login(self):
        self.client.login()
        return self

    def set_client(self, client: OdooClient):
        self.client = client

    def get_username(self):
        return self.api_key.username

    def get_alias(self):
        return self.api_key.alias

    def version(self):
        return self.client.version()

    def fetch_write_date(self, model, ids, *args, **kwargs):
        return self.client.read(model, [ids], {'fields': ['id', 'write_date']})

class OdooBasicAPI(OdooAPIBase):
    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_uom(self) -> List[Dict]:
        res = self.client.search_read('uom.uom', [[]],  {
            'fields': [
                'id', 'name', 'category_id', 'factor',
                'factor_inv', 'rounding', 'uom_type'
            ]
        })
        return res

    def fetch_countries(self) ->List[Dict]:
        res = self.client.search_read('res.country', [[]], {
            'fields': ['id', 'name', 'code']
        })
        return res

    def fetch_titles(self) -> List[Dict]:
        res = self.client.search_read('res.partner.title', [[]],  {'fields': ['id', 'name', 'shortcut']})
        return res


