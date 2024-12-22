
import json
import os
from enum import Enum
from typing import Optional, List
from aiohttp import BasicAuth
from external.lingxing.sdk.openapi import OpenApiBase
from core.config import settings
from external.lingxing.sdk.resp_schema import AccessTokenDto
from core.log import logger


class LingxingClient:
    def __init__(self, host, app_id, app_secret, alias, proxy=None, proxy_auth: BasicAuth=None, *args, **kwargs):
        self.access_token: AccessTokenDto = None
        self.op_api = OpenApiBase(host, app_id, app_secret)
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.alias = alias

    def is_expired(self):
        if not self.access_token:
            flag = True
        elif self.access_token.expires_in < 60:
            flag = True
        else:
            flag = False
        return flag

    async def login(self) -> AccessTokenDto:
        if not self.access_token:
            self.access_token = await self.op_api.generate_access_token()
        return self.access_token

    async def refresh_token(self) -> AccessTokenDto:
        if self.access_token and self.access_token.refresh_token:
            self.access_token = await self.op_api.refresh_token(self.access_token.refresh_token)
        else:
            self.access_token = await self.login()
        return self.access_token

    async def request(self, route_name: str, method: str, req_params: Optional[dict] = None,
                      req_body: Optional[dict] = None, **kwargs):
        if not self.access_token:
            await self.login()
        elif self.is_expired():
            logger.info("Access token expired, refreshing...")
            await self.refresh_token()
        return await self.op_api.request(self.access_token.access_token,
                                         route_name, method, req_params, req_body,
                                         proxy=self.proxy, proxy_auth=self.proxy_auth,
                                         **kwargs)

    @classmethod
    def from_json(cls, key_index, proxy_index=None):
        """
        Loads the API keys from the JSON file
        :param index: Index of the API key to load (default is 0)
        :return:
        """
        # Load the API keys from the JSON file
        file_path = os.path.join('conf', 'apikeys',
                                 settings.LINGXING_ACCESS_KEY)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
            params = data["keys"][key_index]

        if proxy_index is not None:
            file_path = os.path.join('conf', 'apikeys',
                                     settings.HTTP_PROXY)
            with open(file_path, 'r') as fp:
                proxy_data = json.load(fp)
            proxy = proxy_data["proxies"][proxy_index]["url"]
            proxy_auth = BasicAuth(proxy_data["proxies"][proxy_index]["username"],
                                   proxy_data["proxies"][proxy_index]["password"])
            params.update({"proxy": proxy, "proxy_auth": proxy_auth})


        k = cls(**params)
        return k

class ListingClient(LingxingClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    async def __fetch_listings_by_sid(self, sid: str):
        # Get listing
        logger.info(f"Fetching listings for seller {sid}...")
        item_count = 0
        total = 999999
        listings = []
        params = {}
        while item_count < total:
            params['sid'] = sid
            params['offset'] = item_count
            params['length'] = 1000
            resp = await self.request("/erp/sc/data/mws/listing",
                                    "POST",
                                       req_body=params)
            li = resp.data
            item_count += len(li)
            total = resp.total
            listings.extend(li)
        return listings

    async def fetch_seller_id_list(self):
        resp = await self.request("/erp/sc/data/seller/lists", "GET")
        seller_list = resp.data
        list_sid = [f"{seller['sid']}" for seller in seller_list]
        logger.info(f"sid: {list_sid}")
        return list_sid

    async def fetch_listings(self, list_sid: List[int]):
        """
        Fetch listings for multiple sellers
        :param sid: a list of seller id
        :return: list of listings
        """
        listings = []
        for s in list_sid:
            li = await self.__fetch_listings_by_sid(s)
            listings.extend(li)
        logger.info(f"Total Fetched Listing: {len(listings)}")
        filtered_listings = list(filter(lambda l: l['is_delete'] == 0, listings))
        logger.info(f" Filtered Listing: {len(filtered_listings)}")
        return filtered_listings

class WarehouseType(Enum):
    Local = 1
    Oversea = 3

class WarehouseBinType(Enum):
    QualityStorage = 1  # 待检暂存
    AvailableStorage = 2  # 可用暂存
    RejectedStorage = 3 # 次品暂存
    PickStorage = 4 # 拣货暂存
    Available = 5 # 可用
    Rejected = 6 # 次品


class InventoryClient(LingxingClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def fetch_warehouses_ids(self, warehouse_type: WarehouseType=WarehouseType.Local):
        """
        Fetch warehouses
        :return: list of warehouses id
        """
        params = {
            "type": warehouse_type.value,
        }
        resp = await self.request("/erp/sc/data/local_inventory/warehouse", "POST", req_body=params)
        warehouses = resp.data
        logger.info(f"wid: {warehouses}")
        return warehouses

    async def fetch_inventory_bin_details(self, warehouse_id: str, bin_type: WarehouseBinType=WarehouseBinType.Available):
        params = {
            "wid": warehouse_id,
            'bin_type_list': bin_type.value,
            'length': 800,
        }
        resp = await self.request("/erp/sc/routing/data/local_inventory/inventoryBinDetails", "POST", req_body=params)
        inventory_details = resp.data
        total = resp.total
        logger.info(f"Inventory Bin Details: {len(inventory_details)}/{total}")
        return inventory_details

    async def fetch_inventory_details(self, warehouse_id: str):
        params = {
            "wid": warehouse_id,
            'length': 800,
        }
        resp = await self.request("/erp/sc/routing/data/local_inventory/inventoryDetails", "POST", req_body=params)
        inventory_details = resp.data
        total = resp.total
        logger.info(f"Inventory Details: {len(inventory_details)}/{total}")
        return inventory_details

