import asyncio
import io
import os
import warnings
from copy import copy
from datetime import datetime
from typing import List, Optional, Dict
import pandas as pd
from aiohttp import ClientPayloadError
from fastapi import HTTPException
from pydantic import BaseModel, Field
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

import external.lingxing as lx
from core.config2 import settings
from core.log import logger
from crud.lingxing import AsyncLingxingBasicDataDB, AsyncLingxingListingDB, AsyncLingxingInventoryDB, \
    AsyncLingxingFbaShipmentPlanDB, AsyncLingxingOrderDB
from external.lingxing import *
import utils.time as time_utils
from external.lingxing.base import FbaShipmentPlanStatus
from models import SKUReplenishmentProfileModel, SKUReplenishmentProfile_Pydantic
from schemas import Seller, Listing, Inventory
from schemas.lingxing import PrintShopListingVO, Marketplace, FbaShipmentPlan, PrintShopFbaShipmentPlanVO
from utils.stringutils import chinese_to_pinyin
from utils.utils_barcodes import generate_barcode_fnsku
import utils.utilpdf as utilpdf

UPLOAD_DIR = settings.static.upload_dir

class BasicDataService:
    def __init__(self, key_index, proxy_index=None):
        self.client = lx.BasicDataClient.from_json(key_index, proxy_index)
        self.mdb_basic_data = AsyncLingxingBasicDataDB()

    async def __aenter__(self):
        await self.mdb_basic_data.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mdb_basic_data.__aexit__(exc_type, exc_val, exc_tb)


    async def save_all_basic_data(self):
        marketplaces = await self.client.fetch_marketplaces()
        for mkplace in marketplaces:
            document = {
                '_id': mkplace['marketplace_id'],
                'fetchedAt': time_utils.now(),
                'data': mkplace,
                'alias': self.client.alias,
            }
            await self.mdb_basic_data.save_marketplace(document['_id'], document)

        logger.info(f"Saved {len(marketplaces)} marketplaces to database.")

        sellers = await self.client.fetch_sellers()
        for seller in sellers:
            document = {
                '_id': seller['sid'],
                'fetchedAt': time_utils.now(),
                'data': seller,
                'alias': self.client.alias,
            }
            await self.mdb_basic_data.save_seller(document['_id'], document)
        logger.info(f"Saved {len(sellers)} sellers to database.")

    async def find_all_sellers(self, *args, **kwargs) -> List[Seller]:
        sellers = await self.mdb_basic_data.query_all_sellers(*args, **kwargs)
        if sellers:
            sellers: List[Seller] = [self.to_seller(s['data']) for s in sellers]
        ch_to_eng = {
                    # Account name
                    "成都亚马逊": "🌶️CTU",
                     "亚马逊NORD": "❄️NORD",
                     "HansaGT": "🌈HansaGT",
                     # Shopname
                     "15640097175成都亚马逊-DE": "CTU-DE",
                     "亚马逊NORD-DE": "NORD-DE"}
        for s in sellers:
            if s.account_name in ch_to_eng:
                s.account_name = ch_to_eng[s.account_name]
            if s.name in ch_to_eng:
                s.name = ch_to_eng[s.name]
        return sellers

    async def find_seller_by_sid(self, sid: str) -> Seller:
        seller = await self.mdb_basic_data.query_seller(sid)
        if seller:
            return self.to_seller(seller['data'])
        else:
            return None

    async def find_all_marketplaces(self, *args, **kwargs):
        marketplaces = await self.mdb_basic_data.query_all_marketplaces(*args, **kwargs)
        if marketplaces:
            marketplaces = [self.to_marketplace(m['data']) for m in marketplaces]
        return marketplaces

    def to_seller(self, seller_data) -> Seller:
         return Seller(sid=seller_data['sid'], name=seller_data['name'],
                       account_name=seller_data['account_name'],
                       marketplace_id=seller_data['marketplace_id'],
                       status=seller_data['status'],
                       country=seller_data['country'],
                       region=seller_data['region'],)

    def to_marketplace(self, marketplace_data):
        return Marketplace(mid=marketplace_data['mid'],
                           region=marketplace_data['region'],
                           aws_region=marketplace_data['aws_region'],
                           code=marketplace_data['code'],
                           country=marketplace_data['country'],
                           marketplace_id=marketplace_data['marketplace_id'],)


class ListingService:
    def __init__(self, key_index, proxy_index=None):
        self.client = lx.ListingClient.from_json(key_index, proxy_index)
        self.mdb_listing = AsyncLingxingListingDB()
        self.mdb_basic_data = AsyncLingxingBasicDataDB()

    async def __aenter__(self):
        await self.mdb_listing.__aenter__()
        await self.mdb_basic_data.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mdb_listing.__aexit__(exc_type, exc_val, exc_tb)
        await self.mdb_basic_data.__aexit__(exc_type, exc_val, exc_tb)

    async def save_all_listings(self):
        sellers = await self.mdb_basic_data.query_all_sellers()
        list_sids = [s['_id'] for s in sellers]
        listings = await self.client.fetch_listings(list_sids, include_delete=True)
        for ls in listings:
            document = {
                '_id': ls['listing_id'],
                'fetchedAt': time_utils.now(),
                'data': ls,
                'alias': self.client.alias,
            }
            await self.mdb_listing.save_listing(document['_id'], document)
        logger.info(f"Saved {len(listings)} listings to database.")

    async def find_all_listings(self, *args, **kwargs) -> List[Listing]:
        listings = await self.mdb_listing.query_all_listings(*args, **kwargs)
        if listings:
            listings = [self.to_listing(l['data']) for l in listings]
        return listings

    async def find_listing_by_listing_id(self, listing_id: str) -> Listing:
        listing = await self.mdb_listing.query_listings_by_listing_ids([listing_id])
        if listing:
            return self.to_listing(listing[0]['data'])
        else:
            return None

    async def find_listings_by_fnsku(self, fnsku: str) -> List[Listing]:
        listings = await self.mdb_listing.query_listings_by_fnsku(fnsku)
        if listings:
            listings = [self.to_listing(l['data']) for l in listings]
        return listings

    def to_listing(self, listing_data):
        return Listing(listing_id=listing_data['listing_id'],
                       sid=listing_data['sid'],
                       seller_sku=listing_data['seller_sku'],
                       fnsku=listing_data['fnsku'],
                       item_name=listing_data['item_name'],
                       asin=listing_data['asin'],
                       parent_asin=listing_data['parent_asin'],
                       small_image_url=listing_data['small_image_url'],
                       status=listing_data['status'],
                       is_delete=listing_data['is_delete'],
                       local_sku=listing_data['local_sku'],
                       local_name=listing_data['local_name'],
                       price=listing_data['price'],
                       currency_code=listing_data['currency_code'],
                       fulfillment_channel_type=listing_data['fulfillment_channel_type'],
                       label="",)



class WarehouseService:
    def __init__(self, key_index, proxy_index=None):
        self.basic_client = lx.BasicDataClient.from_json(key_index, proxy_index)
        self.client = lx.InventoryClient.from_json(key_index, proxy_index)
        self.mdb_inventory = AsyncLingxingInventoryDB()
        self.warehouses = None
        self.sellers = None

    async def __aenter__(self):
        await self.mdb_inventory.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mdb_inventory.__aexit__(exc_type, exc_val, exc_tb)

    async def get_all_warehouses(self):
        if self.warehouses is None:
            wh_os = await self.client.fetch_warehouses(WarehouseType.Oversea)
            wh_cn = await self.client.fetch_warehouses(WarehouseType.China)
            wh = wh_os + wh_cn
            wh = [w for w in wh if not w["is_delete"]]
            self.warehouses = wh
        return self.warehouses

    async def get_all_sellers(self):
        if self.sellers is None:
            sellers = await self.basic_client.fetch_sellers()
            self.sellers = sellers
        return self.sellers

    async def save_all_inventories(self):
        wh = await self.get_all_warehouses()
        wh_ids = [w['wid'] for w in wh]
        wh_details = await self.client.fetch_inventory_details(wh_ids)
        await self.mdb_inventory.delete_all_inventory()  # Delete all inventory before insert new data
        for wh_detail in wh_details:
            wid = wh_detail['wid']
            seller_id = wh_detail['seller_id']
            product_id = wh_detail['product_id']
            id = f"{wid}_{seller_id}_{product_id}"
            document = {
                '_id': id,
                'fetchedAt': time_utils.now(),
                'data': wh_detail,
                'alias': self.client.alias,
            }
            await self.mdb_inventory.save_inventory(document['_id'], document)
        logger.info(f"Saved {len(wh_details)} inventories to database.")


    async def find_all_inventories(self, *args, **kwargs):
        inventories = await self.mdb_inventory.query_all_inventory(*args, **kwargs)
        return inventories

    async def find_inventory_by_sku(self, sku: str, wid: int=None):
        filter_ = {'data.sku': sku}
        if wid:
            filter_['data.wid'] = wid
        inventories = await self.mdb_inventory.query_inventory(filter=filter_)
        return inventories

    async def find_inventory_by_wid(self, wid: str, *args, **kwargs):
        inventories = await self.mdb_inventory.query_inventory(filter={'data.wid': wid},
                                                               *args, **kwargs)
        return inventories

    async def save_all_inventory_bins(self):
        wh = await self.get_all_warehouses()
        wh_ids = [w['wid'] for w in wh]
        wh_bin_details = await self.client.fetch_inventory_bin_details(wh_ids,
                                                                       bin_type_list=None)
        await self.mdb_inventory.delete_all_inventory_bin()  # Delete all inventory bin before insert new data
        for wh_bin_detail in wh_bin_details:
            wid = wh_bin_detail['wid']
            whb_id = wh_bin_detail['whb_id']
            store_id = wh_bin_detail['store_id']
            product_id = wh_bin_detail['product_id']
            id = f"{wid}_{whb_id}_{store_id}_{product_id}"
            document = {
                '_id': id,
                'fetchedAt': time_utils.now(),
                'data': wh_bin_detail,
                'alias': self.client.alias,
            }
            await self.mdb_inventory.save_inventory_bin(document['_id'], document)
        logger.info(f"Saved {len(wh_bin_details)} inventory bins to database.")

    async def find_all_inventory_bins(self, *args, **kwargs):
        inventory_bins = await self.mdb_inventory.query_all_inventory_bin(*args, **kwargs)
        return inventory_bins

    async def find_inventory_bin_by_whb_id(self, whb_id: str):
        inventory_bins = await self.mdb_inventory.query_inventory_bin(
            filter={'data.whb_id': whb_id}
        )
        return inventory_bins

    async def find_inventory_bin_by_sku(self, sku: str):
        inventory_bins = await self.mdb_inventory.query_inventory_bin(
            filter={'data.sku': sku}
        )
        return inventory_bins

    async def find_inventory_bin_by_wid(self, wid: str):
        inventory_bins = await self.mdb_inventory.query_inventory_bin(
            filter={'data.wid': wid}
        )
        return inventory_bins

    async def find_all_inventory_with_bin(self, wids: List[str]=None, offset=0, limit=100) -> List[Inventory]:
        # TODO: 优化这段代码。多仓库的情况下，这段代码会有问题。
        # TODO: 这段代码查询效率不高，以后需要优化。
        filter_ = {}
        if wids:
            filter_['data.wid'] = {"$in": wids}
        bin_details = await self.mdb_inventory.query_inventory_bin(filter=filter_, offset=0, limit=99999)
        bin_details = [d['data'] for d in bin_details]
        wh_map = {d['wid']: d['wh_name'] for d in bin_details}

        # Create a dataframe for warehouse bin details
        df_whb = pd.DataFrame.from_dict(bin_details) \
            .sort_values(by=['sku', 'validNum'], ascending=False)

        # Aggregate warehouse bin details by sku
        df_whb_agg = df_whb.groupby(['sku']).agg(
            {'validNum': 'sum', 'whb_name': 'first', 'wh_name': 'first', 'product_name': 'first'})
        df_whb_agg = df_whb_agg.reset_index()

        filter_ = {}
        if wids:
            filter_['data.wid'] = {"$in": wids}
        inventory_details = await self.mdb_inventory.query_inventory(filter=filter_, offset=offset, limit=limit)
        inventory_details = [d['data'] for d in inventory_details]
        # Create a dataframe for inventory details
        df_wh = pd.DataFrame.from_dict(inventory_details) \
            .drop(['stock_age_list'], axis=1).sort_values(by=['sku'])
        df_wh['quantity_receive'] = df_wh['quantity_receive'].astype(int)
        # Aggregate inventory details by sku
        df_wh_agg = df_wh.groupby(['sku']).agg({
            'product_valid_num': 'sum', # on hand quantity
            'quantity_receive': 'sum',  # in transit quantity
            'wid': 'first' # warehouse id
        })
        df_wh_agg.reset_index(inplace=True)

        def get_wh_name(row):
            return wh_map[row['wid']] if row['wid'] in wh_map.keys() else ""

        # Left join
        df_left = pd.merge(df_wh_agg, df_whb_agg, on='sku', how='left')
        df_left = df_left[['sku', 'product_valid_num', 'quantity_receive', 'wid', 'whb_name', 'wh_name']]
        # Handle missing values
        df_left['whb_name'] = df_left['whb_name'].fillna("")
        df_left['wh_name'] = df_left.apply(lambda row: get_wh_name(row), axis=1)

        rename_cols = {'sku': 'sku', 'product_valid_num': 'quantity',
                       'quantity_receive': 'in_transit_quantity',
                       'wid': 'warehouse_id',
                        'whb_name': 'storage_location', 'wh_name': 'warehouse_name'}
        df_left.rename(columns=rename_cols, inplace=True)

        inv_dicts = df_left.to_dict(orient='records')
        inventories = [Inventory(**inv_dict) for inv_dict in inv_dicts]
        ch_to_eng = {'可用暂存': 'Stock'}
        for invt in inventories:
            if invt.storage_location in ch_to_eng.keys():
                invt.storage_location = ch_to_eng[invt.storage_location]

        return inventories

    async def save_all_fba_inventories(self):
        sellers = await self.get_all_sellers()
        seller_ids = [s['sid'] for s in sellers]
        wh_details = await self.client.fetch_fba_inventory_details(seller_ids)
        await self.mdb_inventory.delete_all_fba_inventory()
        for wh_details in wh_details:
            document = {
                'fetchedAt': time_utils.now(),
                'data': wh_details,
                'alias': self.client.alias,
            }
            await self.mdb_inventory.save_fba_inventory(
                fba_inventory_id=None,
                document=document
            )
        logger.info(f"Saved {len(wh_details)} FBA inventories to database.")

    async def find_fba_inventories(self, *args, **kwargs):
        inventories = await self.mdb_inventory.query_fba_inventory(*args, **kwargs)
        return inventories

class FbaShipmentPlanService:
    def __init__(self, key_index, proxy_index=None):
        self.client = lx.FbaShipmentPlanClient.from_json(key_index, proxy_index)
        self.mdb_fba_shipment_plan = AsyncLingxingFbaShipmentPlanDB()

    async def __aenter__(self):
        await self.mdb_fba_shipment_plan.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mdb_fba_shipment_plan.__aexit__(exc_type, exc_val, exc_tb)

    async def save_fba_shipment_plans_latest(self, limit=100):
        plans = await self.client.fetch_latest_plans(limit=limit)
        for plan in plans:
            document = {
                '_id': plan['ispg_id'],
                'fetchedAt': time_utils.now(),
                'data': plan,
                'alias': self.client.alias,
            }
            await self.mdb_fba_shipment_plan.save_fba_shipment_plan(document['_id'], document)
        logger.info(f"Saved {len(plans)} FBA shipment plans to database.")

    async def find_fba_all_shipment_plans(self, statuses: List[FbaShipmentPlanStatus]=None,
                                          *args, **kwargs) -> List[FbaShipmentPlan]:
        if statuses:
            filter_ = {'data.list.status': {"$in": [s.value for s in statuses]}}
        else:
            filter_ = {}

        plans = await self.mdb_fba_shipment_plan.query_all_fba_shipment_plans(filter=filter_,*args, **kwargs)
        if plans is None:
            return plans

        subplans= []
        for p in plans:
            subplans.extend(self.to_fba_shipment_plans(p['data']))
        return subplans

    async def find_fba_shipment_plans_by_ispg_id(self, ispg_id: int) -> FbaShipmentPlan:
        plan = await self.mdb_fba_shipment_plan.query_fba_shipment_plan_by_ispg_id(ispg_id)
        if plan is None:
            return plan
        subplans = self.to_fba_shipment_plans(plan['data'])
        return subplans

    async def find_fba_shipment_plans_by_seq_code(self, seq_code: str):
        plan = await self.mdb_fba_shipment_plan.query_fba_shipment_plan_by_seq(seq_code)
        if plan is None:
            return plan
        subplans = self.to_fba_shipment_plans(plan['data'])
        return subplans

    def to_fba_shipment_plans(self, plan_data) -> List[FbaShipmentPlan]:
        subplans = []
        for sub in plan_data['list']:
            subplans.append(self.to_fba_shipment_subplan(sub))
        return subplans

    def to_fba_shipment_subplan(self, subplan_data):
        status_name_cn_en = {
            "已驳回": "Rejected",
            "待审核": "PendingReview",
            "待处理": "Placed",
            "已处理": "Processed",
        }
        status_name = status_name_cn_en.get(subplan_data['status_name'], subplan_data['status_name'])
        return FbaShipmentPlan(
            seq=subplan_data['seq'],
            order_sn=subplan_data['order_sn'],
            sid=subplan_data['sid'],
            create_time=subplan_data['create_time'],
            create_user=subplan_data['create_user'],
            fnsku=subplan_data['fnsku'],
            msku=subplan_data['msku'],
            wname=subplan_data['wname'],
            status=subplan_data['status'],
            status_name=status_name,
            shipment_time=subplan_data['shipment_time'],
            shipment_plan_quantity=subplan_data['shipment_plan_quantity'],
            quantity_in_case=subplan_data['quantity_in_case'],
            box_num=subplan_data['box_num'],
            small_image_url=subplan_data['small_image_url'],
            product_name=subplan_data['product_name'],
            sku=subplan_data['sku'],
            is_combo=subplan_data['is_combo'],
            is_urgent=subplan_data['is_urgent'],
        )



class GeneralService:
    def __init__(self, key_index, proxy_index=None):
        self.key_index = key_index
        self.proxy_index = proxy_index
        self.basic_service = BasicDataService(key_index, proxy_index)
        self.warehouse_service = WarehouseService(key_index, proxy_index)
        self.listing_service = ListingService(key_index, proxy_index)
        self.fba_shipment_plan_service = FbaShipmentPlanService(key_index, proxy_index)

    async def __aenter__(self):
        await self.basic_service.__aenter__()
        await self.warehouse_service.__aenter__()
        await self.listing_service.__aenter__()
        await self.fba_shipment_plan_service.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.basic_service.__aexit__(exc_type, exc_val, exc_tb)
        await self.warehouse_service.__aexit__(exc_type, exc_val, exc_tb)
        await self.listing_service.__aexit__(exc_type, exc_val, exc_tb)
        await self.fba_shipment_plan_service.__aexit__(exc_type, exc_val, exc_tb)

    async def generate_fnsku_label_by_listing_id(self, listing_id: str, quantity: int=1) -> Listing:
        dtime = datetime.now().strftime("%Y-%m-%d")
        listing = await self.listing_service.find_listing_by_listing_id(listing_id)
        if listing:
            fnsku = listing.fnsku
            sku = listing.local_sku
        else:
            raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found.")

        # async with WarehouseService(key_index, proxy_index) as svc_warehouse:
        inventories = await self.warehouse_service.find_all_inventory_with_bin(limit=99999)
        inventories = [inv for inv in inventories if inv.sku == sku]
        inv_str = ""
        if inventories:
            inv_str = ", ".join([f"{inv.storage_location} ({inv.quantity}) | {inv.warehouse_name}" for inv in inventories])

        seller = await self.basic_service.find_seller_by_sid(listing.sid)

        # note = f"[{dtime}] | {inv_str}"
        note = f"{dtime}"
        title = f"[{listing.seller_sku}] {listing.item_name}"
        title = title[:200]
        sku = f"{listing.local_sku} | {seller.name}"
        b64_str = generate_barcode_fnsku(fnsku, sku, title, note)

        # Duplicate code according to the quantity
        label_bytes = utilpdf.str_to_pdf(b64_str)
        w, h = utilpdf.extract_pdf_size(label_bytes)
        label_list = [label_bytes] * quantity
        merged_pdf_bytes = await self.__concat_pdf(label_list)
        pdf_with_page_numbers = await self.__add_page_numbers(
            merged_pdf_bytes,
            page_list=None,
            position=(w / 2 + 50, 10),
        )
        pdf_with_page_numbers = utilpdf.compress_vector_pdf_fiz(pdf_with_page_numbers)
        b64_str = utilpdf.pdf_to_str(pdf_with_page_numbers)

        listing.label = b64_str
        return listing.label

    async def __add_page_numbers(self, *args, **kwargs):
        return await asyncio.to_thread(
            utilpdf.add_page_numbers_fitz,
            *args,
            **kwargs
        )

    async def __concat_pdf(self, *args, **kwargs):
        return await asyncio.to_thread(
            utilpdf.concat_pdfs_fitz,
            *args,
            **kwargs
        )

    async def get_printshop_listing_view(self, offset=0, limit=100, has_fnsku=True, is_unique_fnsku=False,
                                         include_off_sale = False, wids = None, seller_id = None,
                                         *args, **kwargs) -> List[PrintShopListingVO]:
        filter_ = {}
        if not include_off_sale:
            filter_['data.status'] = 1
        if has_fnsku:
            filter_['data.fnsku'] = {"$ne": ""}
        if seller_id is not None:
            filter_['data.sid'] = seller_id

        # TODO: 实现真正的分页查询

        listings = await self.listing_service.find_all_listings(offset=offset, limit=limit, filter_=filter_, *args, **kwargs)

        if is_unique_fnsku:
            unique_listings = []
            seen_fnsku = set()
            for listing in listings:
                if listing.fnsku not in seen_fnsku:
                    unique_listings.append(listing)
                    seen_fnsku.add(listing.fnsku)
            listings = unique_listings

        sellers = await self.basic_service.find_all_sellers()
        marketplaces = await self.basic_service.find_all_marketplaces()
        inventories = await self.warehouse_service.find_all_inventory_with_bin(wids=wids, limit=99999)
        sellers_map = {s.sid: s for s in sellers}
        inv_map = {inv.sku: inv for inv in inventories}
        marketplaces_map = {m.country: m for m in marketplaces}
        view_listings = []
        for listing in listings:
            try:
                inv = copy(inv_map.get(listing.local_sku, None))
                seller = copy(sellers_map.get(listing.sid, None))
                seller.country = marketplaces_map.get(seller.country, None).code
            except Exception as e:
                logger.error(f"Error while processing listing {listing.listing_id}: {e}")

            vo = PrintShopListingVO(
                listing_id=listing.listing_id,
                seller_sku=listing.seller_sku,
                fnsku=listing.fnsku,
                item_name=listing.item_name,
                asin=listing.asin,
                parent_asin=listing.parent_asin,
                small_image_url=listing.small_image_url,
                status=listing.status,
                is_delete=listing.is_delete,
                local_sku=listing.local_sku,
                local_name=listing.local_name,
                price=listing.price,
                currency_code=listing.currency_code,
                fulfillment_channel_type=listing.fulfillment_channel_type,
                seller=seller,
                inventories=[inv] if inv else []
            )
            view_listings.append(vo)
        view_listings = sorted(view_listings, key=lambda x: (x.seller.sid if x.seller else "", x.local_sku))
        return view_listings

    async def get_fba_shipment_plans_view(self, offset=0, limit=100, statuses: List[FbaShipmentPlanStatus]=None,
                                          *args, **kwargs) -> List[PrintShopFbaShipmentPlanVO]:
        plans = await self.fba_shipment_plan_service.find_fba_all_shipment_plans(statuses=statuses, offset=offset,
                                                                                 limit=limit, *args, **kwargs)
        view_plans = []
        sellers = await self.basic_service.find_all_sellers()
        marketplaces = await self.basic_service.find_all_marketplaces()
        inventories = await self.warehouse_service.find_all_inventory_with_bin(limit=99999)
        sellers_map = {s.sid: s for s in sellers}
        inv_map = {inv.sku: inv for inv in inventories}
        marketplaces_map = {m.country: m for m in marketplaces}
        for plan in plans:
            try:
                inv = copy(inv_map.get(plan.sku, None))
                seller = copy(sellers_map.get(plan.sid, None))
                seller.country = marketplaces_map.get(seller.country, None).code
            except Exception as e:
                logger.error(f"Error while processing FBA shipment plan {plan.order_sn}: {e}")

            vo = PrintShopFbaShipmentPlanVO(
                seq=plan.seq,
                order_sn=plan.order_sn,
                sid=plan.sid,
                create_time=plan.create_time,
                create_user=chinese_to_pinyin(plan.create_user, separator=""),
                fnsku=plan.fnsku,
                msku=plan.msku,
                wname=plan.wname,
                status=plan.status,
                status_name=plan.status_name,
                shipment_time=plan.shipment_time,
                shipment_plan_quantity=plan.shipment_plan_quantity,
                quantity_in_case=plan.quantity_in_case,
                box_num=plan.box_num,
                small_image_url=plan.small_image_url,
                product_name=plan.product_name,
                sku=plan.sku,
                is_combo=plan.is_combo,
                is_urgent=plan.is_urgent,
                seller=seller,
                inventories=[inv] if inv else []
            )
            view_plans.append(vo)
        view_plans = sorted(view_plans, key=lambda x: x.create_time, reverse=True)
        return view_plans



# TODO: 打印产品标签
#  https://apidoc.lingxing.com/#/docs/Warehouse/productLabel?id=%e8%af%b7%e6%b1%82%e5%8f%82%e6%95%b0
#  https://apidoc.lingxing.com/#/docs/FBA/printFnskuLabels?id=%e6%9f%a5%e8%af%a2fba%e8%b4%a7%e4%bb%b6%e5%95%86%e5%93%81fnsku%e6%a0%87%e7%ad%be

class LingxingOrderDetail(BaseModel):
    amazon_order_id: str
    purchase_date: str
    name: str
    city: str
    seller: Optional[str]
    fulfillment_channel: str
    order_status: str
    order_total_amount: float
    currency: str
    is_business_order: bool
    buyer_email: str
    buyer_name: str
    postal_code: str
    state_or_region: str
    country_code: str
    address_line1: str
    address_line2: str
    address_line3: str
    sku_content: str
    asin_content: str
    content: str

class OrderService:

    def __init__(self, key_index, proxy_index=None):
        self.key_index = key_index
        self.proxy_index = proxy_index
        self.client = lx.OrderClient.from_json(key_index, proxy_index)
        self.mdb_order = AsyncLingxingOrderDB()

    async def __aenter__(self):
        await self.mdb_order.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mdb_order.__aexit__(exc_type, exc_val, exc_tb)

    async def save_orders(self, days_ago=20):
        offset = 0
        length = 4500
        total = 1e6
        count = 0

        while offset < total:
            try:
                order_resp = await self.client.fetch_orders(
                    order_status=['Shipped'],
                    days_ago=days_ago,
                    offset=offset,
                    length=length,
                )
                total = order_resp.total
                # Save orders to mongodb
                saved_count = await self.__save_orders_to_mongodb(order_resp.data)
                count += saved_count
            except ClientPayloadError as e:
                logger.info(f"Error while fetching orders: {e}")
                await asyncio.sleep(10)
            finally:
                offset += length
        logger.info(f"Saved {count} orders to database")
            

    async def __save_orders_to_mongodb(self, orders: List[Dict]) -> int:
        logger.info(f"Fetched {len(orders)} orders.")
        documents = [{
                "_id": order['amazon_order_id'],
                "fetchedAt": time_utils.now(),
                "data": order,
                "alias": self.client.alias,
            }
            for order in orders
        ]
        count = await self.mdb_order.bulk_save_orders(documents)
        logger.info(f"Saved {count} orders to database.")
        return count

    async def __order_ids_to_fetch_details(self):
        order_ids1 = set(await self.mdb_order.query_all_ids(self.mdb_order.db_collection_orders))
        order_ids2 = set(await self.mdb_order.query_all_ids(self.mdb_order.db_collection_order_details))
        return list(set(order_ids1 - order_ids2))

    def __chunked_iterable(self, lst, chunk_size):
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    async def save_order_details(self):
        logger.info(f"Fetching order details.")
        order_ids = await self.__order_ids_to_fetch_details()
        logger.info(f"Fetching order details for {len(order_ids)} orders.")
        count = 0
        for i, chunked_ids in enumerate(self.__chunked_iterable(order_ids, 180)):
            try:
                print(i, len(chunked_ids), count)
                details_resp = await self.client.fetch_order_details(chunked_ids)
                # Save order details to mongodb
                saved_count = await self.__save_order_details_to_mongodb(details_resp.data)
                count += saved_count
            except ClientPayloadError as e:
                logger.error(f"Error while fetching order details: {e}")
                await asyncio.sleep(10)
        logger.info(f"Saved {count} order details to database.")

    async def __save_order_details_to_mongodb(self, details: List[Dict]):
        logger.info(f"Fetched {len(details)} order details.")
        documents = [{
                "_id": detail["amazon_order_id"],
                "fetchedAt": time_utils.now(),
                "data": detail,
                "alias": self.client.alias,
            }
            for detail in details
        ]
        count = await self.mdb_order.bulk_save_order_details(documents)
        logger.info(f"Saved {count} order details to database.")
        return count

    async def find_order_details(
            self,
            is_business_order: bool,
            limit=None,
            offset=0,
    ):
        filter_ = {
            "data.is_business_order": 1 if is_business_order else 0,
        }
        details = await self.mdb_order.query_order_details(
            offset=offset,
            limit=limit,
            filter=filter_,
        )
        return [self.to_order_detail(detail) for detail in details]

    def to_order_detail(self, order_detail) -> LingxingOrderDetail:
        order_detail = order_detail["data"]
        sku_content = [item['seller_sku'] for item in order_detail['item_list']]
        sku_content = ' | '.join(sku_content)
        asin_content = [item['asin'] for item in order_detail['item_list']]
        asin_content = ' | '.join(asin_content)
        content = [item['title'] for item in order_detail['item_list']]
        content = ' | '.join(content)

        data = {
            "amazon_order_id": order_detail["amazon_order_id"],
            "purchase_date": order_detail["purchase_date_local"],
            "name": order_detail["name"],
            "city": order_detail["city"],
            "seller": order_detail.get("seller", ""),
            "fulfillment_channel": order_detail["fulfillment_channel"],
            "order_status": order_detail["order_status"],
            "order_total_amount": order_detail["order_total_amount"],
            "currency": order_detail["currency"],
            "is_business_order": order_detail["is_business_order"],
            "buyer_email": order_detail['buyer_email'],
            "buyer_name": order_detail['buyer_name'],
            "postal_code": order_detail['postal_code'],
            "state_or_region": order_detail['state_or_region'],
            "country_code": order_detail['country_code'],
            "address_line1": order_detail['address_line1'],
            "address_line2": order_detail['address_line2'],
            "address_line3": order_detail['address_line3'],
            "sku_content": sku_content,
            "asin_content": asin_content,
            "content": content
        }
        detail = LingxingOrderDetail(**data)
        return detail
