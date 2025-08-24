import io
import os
import re
from typing import Optional, Dict

import pandas as pd
from fastapi import HTTPException
from pydantic import BaseModel, Field
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from core.config2 import settings
from core.log import logger
from models import SKUReplenishmentProfileModel, SKUReplenishmentProfile_Pydantic
from services.lingxing import WarehouseService, BasicDataService
UPLOAD_DIR = settings.static.upload_dir

class SKUReplenishmentProfileUpdate(BaseModel):
    alias: Optional[str] = Field(None, description="Alias")
    lead_time: Optional[float] = Field(None, description="Lead time in months")
    units_per_carton: Optional[int] = Field(None, description="Units per carton")
    units_per_fba_carton: Optional[int] = Field(None, description="Units per FBA carton")
    active: Optional[bool] = Field(None, description="Whether active")
    remark: Optional[str] = Field(None, description="Remark")
    updated_by: str = Field(..., description="User who updated this record")


class ReplenishmentBasicService:

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
        raise NotImplementedError

    async def data_collection(self, filename):
        full_filename = UPLOAD_DIR + filename
        df_listing = await self.__load_lingxing_listing_excel(full_filename)
        df_fba_inv = await self.__query_fba_inventories()
        df_lx_inventory = await self.__query_lx_inventories()
        result = await self.get_replenishment_profiles(offset=0, limit=9999)
        df_profiles = pd.DataFrame.from_dict([item.dict() for item in result['data']])
        df_profiles = df_profiles[[
            'local_sku', 'lead_time',
            'units_per_fba_carton', 'alias',
            'units_per_carton', 'active', 'remark'
        ]]
        df_profiles = df_profiles.rename(columns={"local_sku": "sku"})
        return {
            "listing": df_listing,
            "fba_inv": df_fba_inv,
            "lx_inv": df_lx_inventory,
            "profiles": df_profiles
        }

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
        target_columns = ['MSKU', 'FNSKU', 'SKU', '店铺', '状态', 'ASIN', '配送方式', '7日销量', '14日销量', '30日销量',
                          '国家']

        try:
            df_listing = df_listing_raw[target_columns]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"File does not contain required columns {target_columns}.")

        df_listing = df_listing.rename(columns={
            'MSKU': 'msku',
            "FNSKU": "fnsku",
            "SKU": "sku",
            '店铺': "seller",
            "状态": "status",
            "ASIN": "asin",
            "配送方式": "fulfillment_channel",
            "7日销量": "seven_days_volume",
            "14日销量": "fourteen_days_volume",
            "30日销量": "thirty_days_volume",
            "国家": "country"
        })

        # & (df_listing['status'] == "在售")
        filter_condition = (
            df_listing['country'] == '德国') \
            & (df_listing['fulfillment_channel'] == 'FBA'
        )
        df_listing = df_listing[filter_condition]
        return df_listing

    async def __query_fba_inventories(self):
        filter_ = {
            "data.fulfillment_channel_name": "FBA"
        }
        fba_inventories = await self.wh_service.find_fba_inventories(filter=filter_, limit=10000)
        if not fba_inventories:
            raise HTTPException(status_code=404, detail="No FBA inventories found.")

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
        df_fba_inv = df_fba_inv.sort_values(by=['brand_name', 'sku'])
        df_fba_inv = df_fba_inv[df_fba_inv['sid'].isin(sid_list)]
        return df_fba_inv

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

    async def import_replenishment_profiles(self, filename: str, updated_by: str):
        logger.info(f"Importing replenishment profiles from {filename} by {updated_by}")
        full_filename = UPLOAD_DIR + filename
        df_listing = await self.__load_lingxing_listing_excel(full_filename)
        df_fba_inv = await self.__query_fba_inventories()
        sku_to_inv_map = {
            item['sku']: dict(product_name=item['product_name'], brand=item['brand_name'], image=item['image'])
            for _, item in df_fba_inv.iterrows()
        }

        required_cols = {"sku"}
        if not required_cols.issubset(df_listing.columns):
            raise HTTPException(status_code=400, detail="Missing required column: SKU")

        # 只导入已配对的
        df_listing = df_listing.dropna(subset=['sku'])

        inserted, updated = 0, 0
        async with in_transaction():
            for _, row in df_listing.iterrows():
                local_sku = str(row["sku"]).strip()
                # 只导入已配对的
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
                        "updated_by": updated_by
                    }).save()
                    updated += 1
                else:
                    await SKUReplenishmentProfileModel.create(
                        local_sku=local_sku,
                        created_by=updated_by,
                        updated_by=updated_by,
                        **data
                    )
                    inserted += 1
        logger.info(f"Imported replenishment profiles: {inserted} inserted, {updated} updated.")
        return {"inserted": inserted, "updated": updated}

    async def get_replenishment_profiles(self, offset=0, limit=100,
                                         brand=None, keyword=None, **kwargs):
        query = Q()
        if keyword:
            query &= Q(local_sku__icontains=keyword)
            query |= Q(alias__icontains=keyword)
            query |= Q(product_name__icontains=keyword)
        if brand:
            query &= Q(brand=brand)
        qs = SKUReplenishmentProfileModel.filter(query, **kwargs)
        total = await qs.count()
        profiles = qs.order_by("brand", "local_sku").offset(offset).limit(limit)
        results = await SKUReplenishmentProfile_Pydantic.from_queryset(profiles)
        return {
            "total": total,
            "data": results
        }

    async def update_replenishment_profile(self, id: int, update_data: SKUReplenishmentProfileUpdate):
        logger.info(f"Updating replenishment profile {id}: {update_data.dict()}")
        obj = await SKUReplenishmentProfileModel.get_or_none(id=id)
        if not obj:
            raise HTTPException(status_code=404, detail="Replenishment profile not found")

        update_dict = update_data.dict(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(obj, k, v)
        try:
            await obj.save()
            result = await SKUReplenishmentProfile_Pydantic.from_tortoise_orm(obj)
        except IntegrityError as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"Duplicate SKU: {obj.local_sku}")
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=f"Failed to update replenishment profile: {e}")
        return result.dict()

    async def delete_replenishment_profile(self, id: int):
        logger.info(f"Deleting replenishment profile {id}")
        obj = await SKUReplenishmentProfileModel.get_or_none(id=id)
        if not obj:
            raise HTTPException(status_code=404, detail="Replenishment profile not found")
        await obj.delete()
        deleted = 1
        return {"deleted": deleted}

    async def get_replenishment_profile_filters(self):
        brands = await SKUReplenishmentProfileModel.all().distinct().values_list("brand", flat=True)
        return {
            "brands": brands,
            "sort_by": ["brand", "local_sku", "created_at", "updated_at"],
            "sort_order": ["asc", "desc"],
        }

    def to_excel(self, df_reports: Dict[str, pd.DataFrame]) -> io.BytesIO:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            for sheet_name, df_report in df_reports.items():
                df_report.to_excel(writer, index=False, sheet_name=sheet_name)
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
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


class WarehouseReplenishmentService(ReplenishmentBasicService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def create_replenishment_report(self, filename):
        # Collection of raw data
        collections = await self.data_collection(filename)
        df_listing = collections['listing']
        df_fba_inv = collections['fba_inv']
        df_lx_inventory = collections['lx_inv']
        df_profiles = collections['profiles']

        # Aggregation
        grouped_df_listing = df_listing.groupby('sku', as_index=False).agg({
            'seller': lambda x: ', '.join(sorted(set(x))),
            'status': lambda x: ', '.join(sorted(set(x))),
            'seven_days_volume': "sum",
            'fourteen_days_volume': "sum",
            'thirty_days_volume': "sum",
        })

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

        grouped_df_lx_inventory = df_lx_inventory.groupby("product_id", as_index=False).agg({
            "sku": "first",
            "on_hand_quantity": "sum",
            "in_transit_quantity": "sum",
        })

        # Merge the dataframes
        df_merged = pd.merge(grouped_df_listing, grouped_df_fba_inv, on='sku', how='left')
        df_merged = pd.merge(df_merged, grouped_df_lx_inventory, on='sku', how='inner')
        df_merged = pd.merge(df_merged, df_profiles, on='sku', how='left')

        # Calculation
        df_replenishment = self.__calculate_replenishment_fields(df_merged)
        df_replenishment = df_replenishment[df_replenishment['active'] == True]

        # Rename columns
        df_replenishment = self.__rename_columns(df_replenishment)

        return df_replenishment

    def __rename_columns(self, df_replenishment):
        EN_TO_CN = {
            'sku': 'SKU',
            "image": "图片",
            'msku': 'MSKU',
            'seller': "店铺",
            'brand_name': '品牌',
            'fnsku': 'FNSKU',
            'status': '状态',
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
            'reorder_quantity': '囤货计算(件)',
            'units_per_carton': '单箱数量',
            'reorder_carton_quantity': "囤货计算(箱)",
            'in_transit_quantity': '在途库存',
            'remark': '备注',
        }

        cols = list(EN_TO_CN.keys())
        df_replenishment = df_replenishment[cols]
        df_replenishment = df_replenishment.rename(columns=EN_TO_CN)
        return df_replenishment

    def __calculate_replenishment_fields(self, df):
        df['total_quantity'] = df['on_hand_quantity'] + df['in_transit_quantity'] \
                               + df['afn_inbound_shipped_quantity'] + df[
                                   'afn_fulfillable_quantity'] + df['total_reserved_quantity']
        df['thirty_days_sell_through'] = round(df['thirty_days_volume'] / df['total_quantity'], 2)
        w_7d, w_14d, w_30d = 4, 2, 1
        df['weighted_lead_time_demand'] = (w_7d * df['seven_days_volume']
                                           + w_14d * df['fourteen_days_volume']
                                           + w_30d * df['thirty_days_volume'])
        df['weighted_lead_time_demand'] = df['weighted_lead_time_demand'] / 3  # 加权平均之后的月销量
        df['weighted_lead_time_demand'] = df['weighted_lead_time_demand'].round(2)
        df['lead_time_demand'] = round(
            df['weighted_lead_time_demand'] * df['lead_time'])  # 计算采购周期内预期会销售出去的数量
        df['reorder_quantity'] = df['lead_time_demand'] - df['total_quantity']
        df['reorder_carton_quantity'] = df['reorder_quantity'] / df['units_per_carton']
        df['reorder_carton_quantity'] = df['reorder_carton_quantity'].round(0)
        # 按照补货排序，而不是sku
        df.sort_values(by=['brand_name', 'reorder_quantity'],
                       ascending=[True, False],
                       inplace=True)
        return df


class AmazonWarehouseReplenishmentService(ReplenishmentBasicService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def create_replenishment_report(self, filename):
        logger.info(f"Creating replenishment report from {filename}")
        # Collection of raw data
        collections = await self.data_collection(filename)
        df_listing = collections['listing']
        df_fba_inv = collections['fba_inv']
        df_lx_inventory = collections['lx_inv']
        df_profiles = collections['profiles']

        # Aggregation
        grouped_df_listing = df_listing.groupby(['fnsku', 'seller'], as_index=False).agg({
            'status': lambda x: ', '.join(sorted(set(x))),
            'seven_days_volume': "sum",
            'fourteen_days_volume': "sum",
            'thirty_days_volume': "sum",
        })

        grouped_df_fba_inv = df_fba_inv.groupby(["sid", "msku"], as_index=False).agg({
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

        grouped_df_lx_inventory = df_lx_inventory.groupby("product_id", as_index=False).agg({
            "sku": "first",
            "on_hand_quantity": "sum",
            "in_transit_quantity": "sum",
        })

        # Merge the dataframes
        df_merged = pd.merge(grouped_df_listing, grouped_df_fba_inv, on='fnsku', how='inner')
        df_merged = pd.merge(df_merged, grouped_df_lx_inventory, on='sku', how='left')
        df_merged = pd.merge(df_merged, df_profiles, on='sku', how='left')

        df_merged.loc[:, 'on_hand_quantity'] = df_merged['on_hand_quantity'].fillna(0)
        df_merged.loc[:, 'in_transit_quantity'] = df_merged['in_transit_quantity'].fillna(0)
        df_merged.loc[:, 'units_per_fba_carton'] = df_merged['units_per_fba_carton'].fillna(1)

        # Calculation
        df_replenishment = self.__calculate_replenishment_fields(df_merged)
        df_replenishment = df_replenishment[df_replenishment['active'] == True]

        # Rename columns
        df_replenishment = self.__rename_columns(df_replenishment)
        return df_replenishment

    def __rename_columns(self, df_replenishment):
        EN_TO_CN = {
            'sku': 'SKU',
            "image": "图片",
            'msku': 'MSKU',
            'seller': "店铺",
            'brand_name': '品牌',
            'fnsku': 'FNSKU',
            'status': "状态",
            'product_name': '产品名称',
            'total_quantity': 'FBA总库存',
            'afn_fulfillable_quantity': 'FBA可售',
            'afn_inbound_shipped_quantity': 'FBA在途',
            'total_reserved_quantity': 'FBA正在接收',
            'on_hand_quantity': '德国仓库存',
            'seven_days_volume': '7日销量',
            'fourteen_days_volume': '14日销量',
            'thirty_days_volume': '30日销量',
            'inv_age_0_to_30_days': "0-30天库龄",
            'thirty_days_sell_through': '30天动销比',
            'weighted_lead_time_demand': '加权平均月销量 (4/2/1)',
            'fba_replenish_quantity': 'FBA补货量(件)',
            'units_per_fba_carton': 'FBA单箱数量',
            'fba_replenish_carton_quantity': 'FBA补货量(箱)',
            'fba_replenish_expression': 'FBA补货表达式',
            'in_transit_quantity': '在途库存',
            'is_stock_enough': '德国仓库存状态',
            'days_until_oos': "断货天数",
            'remark': '备注',
        }

        cols = list(EN_TO_CN.keys())
        df_replenishment = df_replenishment[cols]
        df_replenishment = df_replenishment.rename(columns=EN_TO_CN)
        return df_replenishment

    def __create_fba_replenish_expression(self, row):
        units = row['fba_replenish_quantity']
        sku = row['sku'] if pd.isna(row['alias']) else row['alias']
        if units < 1:
            return ""

        pattern = r"^([A-Z]+)-(.+?)(?:PK(\d+))?$"
        match = re.match(pattern, sku)
        if not match:
            return "无法生成表达式, 请规范SKU格式"

        cartons = row['fba_replenish_carton_quantity']
        units_per_carton = row['units_per_fba_carton']
        expr = f"{units}×({sku})"
        if units_per_carton > 1:
            expr += f"={cartons}ctn"
        return expr

    def __calculate_replenishment_fields(self, df):
        round_to_nearest_half = lambda x: round(x * 2) / 2

        df['total_quantity'] = df['afn_inbound_shipped_quantity'] + df['afn_fulfillable_quantity'] + df['total_reserved_quantity']

        df['thirty_days_sell_through'] = round(df['thirty_days_volume'] / df['total_quantity'], 2)
        w_7d, w_14d, w_30d = 4, 2, 1
        df['weighted_lead_time_demand'] = (w_7d * df['seven_days_volume']
                                           + w_14d * df['fourteen_days_volume']
                                           + w_30d * df['thirty_days_volume'])
        df['weighted_lead_time_demand'] = df['weighted_lead_time_demand'] / 3  # 加权平均之后的月销量
        df['weighted_lead_time_demand'] = df['weighted_lead_time_demand'].round(2)

        df['fba_replenish_quantity'] = df['weighted_lead_time_demand'] - df['total_quantity']
        df['fba_replenish_carton_quantity'] = df['fba_replenish_quantity'] / df['units_per_fba_carton']
        # df['fba_replenish_carton_quantity'] = round_to_nearest_half(df['fba_replenish_carton_quantity'])
        df['fba_replenish_carton_quantity'] = df['fba_replenish_carton_quantity'].round(1)

        df['fba_replenish_quantity'] = df['fba_replenish_quantity'].round(0).astype(int)
        df['fba_replenish_carton_quantity'] = df['fba_replenish_carton_quantity'].round(1)

        df['fba_replenish_expression'] = df.apply(self.__create_fba_replenish_expression, axis=1)

        # 德国仓库存是否足够发货
        df['is_stock_enough'] = df['fba_replenish_quantity'] < df['on_hand_quantity']
        df['is_stock_enough'] = df['is_stock_enough'].apply(lambda x: '' if x else '库存不足')

        # 估算还能撑多少天
        df['days_until_oos'] = df['total_quantity'] / df['weighted_lead_time_demand'] * 30
        df['days_until_oos'] = df['days_until_oos'].round(1)

        # 按照补货排序，而不是sku
        df.sort_values(
            by=['seller', 'brand_name', 'fba_replenish_quantity'],
            ascending=[True, True, False],
            inplace=True)
        return df

