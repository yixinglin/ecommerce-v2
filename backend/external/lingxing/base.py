import json
import os
from enum import Enum
from typing import Optional, List
from aiohttp import BasicAuth
from external.lingxing.sdk.openapi import OpenApiBase
from core.config2 import settings
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
                                 settings.api_keys.lingxing_access_key)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
            params = data["keys"][key_index]

        if proxy_index is not None:
            file_path = os.path.join('conf', 'apikeys',
                                     settings.http_proxy.config_file)
            with open(file_path, 'r') as fp:
                proxy_data = json.load(fp)
            proxy = proxy_data["proxies"][proxy_index]["url"]
            proxy_auth = BasicAuth(proxy_data["proxies"][proxy_index]["username"],
                                   proxy_data["proxies"][proxy_index]["password"])
            params.update({"proxy": proxy, "proxy_auth": proxy_auth})


        k = cls(**params)
        return k

class BasicDataClient(LingxingClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def fetch_sellers(self):
        resp = await self.request("/erp/sc/data/seller/lists", "GET")
        seller_list = resp.data
        # list_sid = [f"{seller['sid']}" for seller in seller_list]
        # logger.info(f"sellers: {seller_list}")
        return seller_list

    async def fetch_marketplaces(self):
        resp = await self.request("/erp/sc/data/seller/allMarketplace", "GET")
        marketplace_list = resp.data
        return marketplace_list

class ListingClient(LingxingClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    """
    Listings API
    """
    async def __fetch_listings_by_sid(self, sid: int):
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

    async def fetch_listings(self, list_sid: List[int], include_delete=False):
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
        if not include_delete:
            listings = list(filter(lambda l: l['is_delete'] == 0, listings))
        logger.info(f" Filtered Listing: {len(listings)}")
        return listings

"""
状态：
-5、已驳回，
0、待审核，
5、待处理，
10、已处理
"""
class FbaShipmentPlanStatus(Enum):
    Rejected: int = -5  # 已驳回
    PendingReview: int = 0 # 待审核
    Placed: int = 5 # 待处理
    Processed: int = 10 # 已处理


class FbaShipmentPlanClient(LingxingClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    async def fetch_unshipped_plans(self):
        """
        Complete fetch unshipped plans
        :return:
        """
        params = {
            "status": FbaShipmentPlanStatus.Placed.value,
            "length": 1000,
        }
        resp = await self.request("/erp/sc/data/fba_report/shipmentPlanLists", "POST",
                                  req_body=params)
        plan_list = resp.data
        return plan_list

    async def fetch_latest_plans(self, limit: int=100):
        params = {
            "length": limit,
        }
        resp = await self.request("/erp/sc/data/fba_report/shipmentPlanLists", "POST",
                                  req_body=params)
        plan_list = resp.data
        return plan_list

class WarehouseType(Enum):
    China = 1
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

    async def fetch_warehouses(self, warehouse_type: WarehouseType=WarehouseType.China):
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

    async def __fetch_inventory_bin_details_by_wid(self, warehouse_id: int, bin_type_list: List[WarehouseBinType]):
        logger.info(f"Fetching inventory bin details for warehouse {warehouse_id}...")
        item_count = 0
        total = 99999
        bin_details = []
        params = {}
        params['wid'] = warehouse_id
        params['length'] = 800
        if bin_type_list is not None and len(bin_type_list) > 0:
            params['bin_type_list'] = ",".join((str(bin_type.value) for bin_type in bin_type_list))

        while item_count < total:
            params['offset'] = item_count
            resp = await self.request("/erp/sc/routing/data/local_inventory/inventoryBinDetails",
                                      "POST", req_body=params)
            bin_d = resp.data
            item_count += len(bin_d)
            total = resp.total
            bin_details.extend(bin_d)
        return bin_details

    async def fetch_inventory_bin_details(self, list_wid: List[int], bin_type_list: List[WarehouseBinType]):
        bin_details = []
        for wid in list_wid:
            bin_d = await self.__fetch_inventory_bin_details_by_wid(wid, bin_type_list)
            bin_details.extend(bin_d)
        logger.info(f"Total Fetched Bin Details: {len(bin_details)}")
        return bin_details

    async def __fetch_inventory_details_by_wid(self, wid: int):
        logger.info(f"Fetching inventory for warehouse {wid}...")
        item_count = 0
        total = 99999
        inventories = []
        params = {}
        while item_count < total:
            params['wid'] = wid
            params['offset'] = item_count
            params['length'] = 800
            resp = await self.request("/erp/sc/routing/data/local_inventory/inventoryDetails",
                                      "POST", req_body=params)
            inv = resp.data
            item_count += len(inv)
            total = resp.total
            inventories.extend(inv)
        return inventories

    async def fetch_inventory_details(self, list_wid: List[int]):
        inventories = []
        # resp = await self.request("/erp/sc/routing/data/local_inventory/inventoryDetails", "POST", req_body=params)
        for wid in list_wid:
            inv = await self.__fetch_inventory_details_by_wid(wid)
            inventories.extend(inv)
        logger.info(f"Total Fetched Inventory: {len(inventories)}")
        return inventories

