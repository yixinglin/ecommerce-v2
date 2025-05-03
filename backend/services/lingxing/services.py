import io
import os
from copy import copy
from datetime import datetime
from typing import List, Optional
import pandas as pd
from fastapi import HTTPException
from pydantic import BaseModel, Field
from tortoise.transactions import in_transaction

import external.lingxing as lx
from core.config2 import settings
from core.log import logger
from crud.lingxing import AsyncLingxingBasicDataDB, AsyncLingxingListingDB, AsyncLingxingInventoryDB, \
    AsyncLingxingFbaShipmentPlanDB
from external.lingxing import *
import utils.time as time_utils
from external.lingxing.base import FbaShipmentPlanStatus
from models import SKUReplenishmentProfileModel, SKUReplenishmentProfile_Pydantic
from schemas import Seller, Listing, Inventory
from schemas.lingxing import PrintShopListingVO, Marketplace, FbaShipmentPlan, PrintShopFbaShipmentPlanVO
from utils.stringutils import chinese_to_pinyin
from utils.utils_barcodes import generate_barcode_fnsku

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
        # Aggregate inventory details by sku
        df_wh_agg = df_wh.groupby(['sku']).agg({'product_valid_num': 'sum', 'wid': 'first'})
        df_wh_agg.reset_index(inplace=True)

        def get_wh_name(row):
            return wh_map[row['wid']] if row['wid'] in wh_map.keys() else ""

        # Left join
        df_left = pd.merge(df_wh_agg, df_whb_agg, on='sku', how='left')
        df_left = df_left[['sku', 'product_valid_num', 'wid', 'whb_name', 'wh_name']]
        # Handle missing values
        df_left['whb_name'] = df_left['whb_name'].fillna("")
        df_left['wh_name'] = df_left.apply(lambda row: get_wh_name(row), axis=1)

        rename_cols = {'sku': 'sku', 'product_valid_num': 'quantity', 'wid': 'warehouse_id',
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

class SKUReplenishmentProfileUpdate(BaseModel):
    lead_time: Optional[float] = Field(None, description="Lead time in months")
    units_per_carton: Optional[int] = Field(None, description="Units per carton")
    active: Optional[bool] = Field(None, description="Whether active")
    remark: Optional[str] = Field(None, description="Remark")
    updated_by: str = Field(..., description="User who updated this record")

class ReplenishmentService:

    def __init__(self, key_index, proxy_index=None):
        self.wh_service = WarehouseService(key_index, proxy_index)
        self.basic_service = BasicDataService(key_index, proxy_index)

    async def __aenter__(self):
        await self.basic_service.__aenter__()
        await self.wh_service.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.basic_service.__aexit__(exc_type, exc_val, exc_tb)
        await self.wh_service.__aexit__(exc_type, exc_val, exc_tb)

    async def create_replenishment_report(self, filename):
        full_filename =UPLOAD_DIR + filename
        df_listing = await self.__load_lingxing_listing_excel(full_filename)
        df_fba_inv, _ = await self.__query_fba_inventories()
        df_lx_inventory = await self.__query_lx_inventories()
        result = await self.get_replenishment_profiles(offset=0, limit=9999)
        df_profiles = pd.DataFrame.from_dict([item.dict() for item in result['data']])
        df_profiles = df_profiles[['local_sku', 'lead_time', 'units_per_carton', 'active', 'remark']]
        df_profiles = df_profiles.rename(columns={"local_sku": "sku"})        

        # Group the dataframes by sku
        grouped_df_listing = self.__aggregate_listing(df_listing)

        grouped_df_fba_inv = self.__aggregate_fba_inventories(df_fba_inv)

        grouped_df_lx_inventory = self.__aggregate_lx_inventories(df_lx_inventory)

        # Merge the dataframes
        df_merged = pd.merge(grouped_df_listing, grouped_df_fba_inv, on='sku', how='left')
        df_merged = pd.merge(df_merged, grouped_df_lx_inventory, on='sku', how='inner')
        df_merged = pd.merge(df_merged, df_profiles, on='sku', how='left')

        # Calculate the columns
        df_replenishment = self.__calculate_replenishment_fields(df_merged.copy())
        df_replenishment = df_replenishment[df_replenishment['active'] == True]

        EN_TO_CN = {
            'sku': 'SKU',
            "image": "图片",
            'msku': 'MSKU',
            'brand_name': '品牌',
            'units_per_carton': '单箱数量',
            'fnsku': 'FNSKU',
            'product_name': '产品名称',
            'total_quantity': '总库存',
            'afn_fulfillable_quantity': 'FBA可售',
            'afn_inbound_shipped_quantity': 'FBA在途',
            'total_reserved_quantity': 'FBA正在接收',
            'on_hand_quantity': '德国仓库存',
            'seven_days_volume': '7日销量',
            'fourteen_days_volume': '14日销量',
            'thirty_days_volume': '30日销量',
            'inv_age_0_to_30_days': "0-30天库龄",
            'inv_age_0_to_90_days': "0-90天库龄",
            'thirty_days_sell_through': '30天动销比',
            'weighted_lead_time_demand': '加权平均月销量 (4/2/1)',
            'lead_time': '补货周期',
            'reorder_quantity': '囤货计算',
            'in_transit_quantity': '在途库存',
            'remark': '备注',
        }

        cols = list(EN_TO_CN.keys())
        df_replenishment = df_replenishment[cols]
        df_replenishment = df_replenishment.rename(columns=EN_TO_CN)
        return df_replenishment

    async def import_replenishment_profiles(self, filename):
        full_filename =UPLOAD_DIR + filename
        df_listing = await self.__load_lingxing_listing_excel(full_filename)
        df_fba_inv, _ = await self.__query_fba_inventories()
        sku_to_inv_map = {
            item['sku']: dict(product_name=item['product_name'], brand=item['brand_name'], image=item['image'])
                for _, item in df_fba_inv.iterrows()
        }

        required_cols = {"sku"}
        if not required_cols.issubset(df_listing.columns):
            raise HTTPException(status_code=400, detail="Missing required column: SKU")

        inserted, updated = 0, 0
        async with in_transaction():
            for _, row in df_listing.iterrows():
                local_sku = str(row["sku"]).strip()
                if not local_sku:
                    continue
                obj = await SKUReplenishmentProfileModel.get_or_none(local_sku=local_sku)
                data = {
                    "brand": sku_to_inv_map.get(local_sku, {}).get("brand", ""),
                    "product_name": sku_to_inv_map.get(local_sku, {}).get("product_name", ""),
                    "image": sku_to_inv_map.get(local_sku, {}).get("image", ""),
                }

                if obj:
                    await obj.update_from_dict({
                        **data,
                        "updated_by": "import"
                    }).save()
                    updated += 1
                else:
                    await SKUReplenishmentProfileModel.create(
                        local_sku=local_sku,
                        created_by="import",
                        updated_by="import",
                        **data
                    )
                    inserted += 1

        return {"inserted": inserted, "updated": updated}


    async def get_replenishment_profiles(self, offset=0, limit=100, **kwargs):
        qs = SKUReplenishmentProfileModel.filter(**kwargs)
        total = await qs.count()
        profiles = qs.order_by("brand", "local_sku").offset(offset).limit(limit)
        results = await SKUReplenishmentProfile_Pydantic.from_queryset(profiles)
        return {
            "total": total,
            "data": results
        }

    async def update_replenishment_profile(self, id: int, update_data: SKUReplenishmentProfileUpdate):
        obj = await SKUReplenishmentProfileModel.get_or_none(id=id)
        if not obj:
            raise HTTPException(status_code=404, detail="Replenishment profile not found")

        update_dict = update_data.dict(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(obj, k, v)
        await obj.save()
        result = await SKUReplenishmentProfile_Pydantic.from_tortoise_orm(obj)
        return result.dict()

    async def delete_replenishment_profile(self, id: int):
        obj = await SKUReplenishmentProfileModel.get_or_none(id=id)
        if not obj:
            raise HTTPException(status_code=404, detail="Replenishment profile not found")
        await obj.delete()
        deleted = 1
        return {"deleted": deleted}

    def to_excel(self, df_report: pd.DataFrame) -> io.BytesIO:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_report.to_excel(writer, index=False, sheet_name='Report')
            workbook = writer.book
            worksheet = writer.sheets['Report']
            # 冻结首行
            worksheet.freeze_panes(1, 0)

            # 设置首行自动换行
            wrap_format = workbook.add_format({'text_wrap': True,
                                               'valign': 'top',
                                               'align': 'center',
                                               'bold': True})
            for col_num, value in enumerate(df_report.columns):
                worksheet.write(0, col_num, value, wrap_format)
        buffer.seek(0)
        return buffer

    async def __load_lingxing_listing_excel(self, filename):
        """
        Read a xlsx file exported from Listing Page on Lingxing
        :param filename:
        :return:
        """
        # Check if the file is valid
        if not os.path.isfile(filename):
            raise HTTPException(status_code=404, detail=f"File {filename} not found.")
        if not filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail=f"File {filename} is not a valid xlsx file.")

        # Read the file and filter the data
        df_listing_raw = pd.read_excel(filename)
        target_columns = ['MSKU', 'FNSKU', 'SKU',  '状态', 'ASIN', '配送方式', '7日销量', '14日销量', '30日销量', '国家']

        try:
            df_listing = df_listing_raw[target_columns]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"File does not contain required columns {target_columns}.")

        df_listing = df_listing.rename(columns={
            'MSKU': 'msku',
            "FNSKU": "fnsku",
            "SKU": "sku",
            "状态": "status",
            "ASIN": "asin",
            "配送方式": "fulfillment_channel",
            "7日销量": "seven_days_volume",
            "14日销量": "fourteen_days_volume",
            "30日销量": "thirty_days_volume",
            "国家": "country"
        })

        filter_condition = (df_listing['country'] == '德国') \
                           & (df_listing['status'] == "在售") \
                           & (df_listing['fulfillment_channel'] == 'FBA')
        df_listing = df_listing[filter_condition]
        df_listing = df_listing.dropna(subset=['sku'])
        return df_listing

    def __aggregate_listing(self, df_listing):
        grouped_df_listing = df_listing.groupby('sku', as_index=False).agg({
            'seven_days_volume': "sum",
            'fourteen_days_volume': "sum",
            'thirty_days_volume': "sum",
        })
        return grouped_df_listing

    async def __query_fba_inventories(self):
        filter_ = {
            "data.fulfillment_channel_name": "FBA"
        }
        fba_inventories = await self.wh_service.find_fba_inventories(filter=filter_, limit=10000)
        sellers = await self.basic_service.find_all_sellers()
        sid_list = [s.sid for s in sellers if s.country == '德国']
        fba_inv_list = []
        for item in list(fba_inventories):
            item = item['data']
            inv = {
                "sid": item['sid'],
                "asin": item['asin'],
                'fnsku': item['fnsku'],
                'msku': item['msku'],
                'sku': item['sku'],
                'is_pair': item['sku'] != "",
                "name": item['name'],
                'product_name': item['product_name'],
                'brand_name': item['brand_name'],
                'image': item['product_image'],
                'afn_fulfillable_quantity': item['afn_fulfillable_quantity'],
                'afn_inbound_shipped_quantity': item['afn_inbound_shipped_quantity'],
                'total_reserved_quantity': int(item['reserved_fc_transfers'])  # 预约出库
                                           + int(item['reserved_fc_processing'])  # 预约处理
                                           + int(item['reserved_customerorders']),  # 预约订单
                'inv_age_0_to_90_days': item['inv_age_0_to_90_days'],
                'inv_age_0_to_30_days': item['inv_age_0_to_30_days'],
                'inv_age_31_to_60_days': item['inv_age_31_to_60_days'],
                'inv_age_61_to_90_days': item['inv_age_61_to_90_days'],
                'fulfillment_channel_name': item['fulfillment_channel_name'],
            }
            fba_inv_list.append(inv)

        df_fba_inv = pd.DataFrame.from_dict(fba_inv_list)
        df_fba_inv_unpair = df_fba_inv[(df_fba_inv['is_pair'] == False)]
        df_fba_inv = df_fba_inv[(df_fba_inv['is_pair'] == True)]
        df_fba_inv = df_fba_inv.sort_values(by=['brand_name', 'sku'])
        df_fba_inv = df_fba_inv[df_fba_inv['sid'].isin(sid_list)]
        df_fba_inv_unpair = df_fba_inv_unpair[df_fba_inv_unpair['sid'].isin(sid_list)]
        return df_fba_inv, df_fba_inv_unpair

    def __aggregate_fba_inventories(self, df_fba_inv):
        grouped_df_fba_inv = df_fba_inv.groupby("sku", as_index=False).agg({
            "sku": "first",
            "asin": lambda x: ', '.join(sorted(set(x))),
            "msku": lambda x: ', '.join(sorted(set(x))),
            "fnsku": lambda x: ', '.join(sorted(set(x))),
            "is_pair": "first",
            "product_name": "first",
            "image": "first",
            "brand_name": "first",
            "afn_fulfillable_quantity": "sum",
            "afn_inbound_shipped_quantity": "sum",
            "total_reserved_quantity": "sum",
            "inv_age_0_to_90_days": "max",
            'inv_age_0_to_30_days': "max",
            'inv_age_31_to_60_days': "max",
            'inv_age_61_to_90_days': "max"
        })
        return grouped_df_fba_inv


    async def __query_lx_inventories(self):
        inventories = await self.wh_service.find_all_inventories(limit=99999)
        lx_inv_list = []
        for item in inventories:
            item = item['data']
            lx_inv_list.append({
                "wid": item['wid'],
                "product_id": item['product_id'],
                "seller_id": item['seller_id'],
                "sku": item['sku'],
                "on_hand_quantity": item['product_valid_num'],  # 有效库存
                "in_transit_quantity": int(item['quantity_receive']),  # 待到货
            })
        df_lx_inventory = pd.DataFrame.from_dict(lx_inv_list)
        return df_lx_inventory

    def __aggregate_lx_inventories(self, df_lx_inventory):
        grouped_df_lx_inventory = df_lx_inventory.groupby("product_id", as_index=False).agg({
            "sku": "first",
            "on_hand_quantity": "sum",
            "in_transit_quantity": "sum",
        })
        return grouped_df_lx_inventory

    def __calculate_replenishment_fields(self, df):
        df['total_quantity'] = df['on_hand_quantity'] + df['in_transit_quantity'] \
                                      + df['afn_inbound_shipped_quantity'] + df[
                                          'afn_fulfillable_quantity'] + df['total_reserved_quantity']
        df['thirty_days_sell_through'] = round(df['thirty_days_volume'] / df['total_quantity'], 2)
        w_7d, w_14d, w_30d = 4, 2, 1
        df['weighted_lead_time_demand'] =   (w_7d * df['seven_days_volume']
                                           + w_14d * df['fourteen_days_volume']
                                           + w_30d * df['thirty_days_volume'])
        df['weighted_lead_time_demand'] = df['weighted_lead_time_demand'] / 3  # 加权平均之后的月销量
        df['weighted_lead_time_demand'] = df['weighted_lead_time_demand'].round(2)
        df['lead_time_demand'] = round(
            df['weighted_lead_time_demand'] * df['lead_time'])  # 计算采购周期内预期会销售出去的数量
        df['reorder_quantity'] = df['lead_time_demand'] - df['total_quantity']
        # 按照补货排序，而不是sku
        df.sort_values(by=['brand_name', 'reorder_quantity'],
                       ascending=[True, False],
                       inplace=True)
        return df




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

    async def generate_fnsku_label_by_listing_id(self, listing_id: str) -> Listing:
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
        b64 = generate_barcode_fnsku(fnsku, sku, title, note)
        listing.label = b64
        return listing.label

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


