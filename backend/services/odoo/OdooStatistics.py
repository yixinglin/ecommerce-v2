import datetime

import pandas as pd

from core.log import logger
from external.odoo import OdooAPIKey
from external.odoo.base import OdooAPIBase


class OdooStatisticsService:

    def __init__(self, key_index, *args, **kwargs):
        api_key = OdooAPIKey.from_json(key_index)
        self.api = OdooAPIBase(api_key, **kwargs)
        self.alias = self.api.get_alias()
        self.username = self.api.get_username()
        logger.info(f"Odoo username: {self.username} ({self.alias})")

    # Get sales data grouped by product_id
    def _get_sales_data(self, from_date: str):
        cli = self.api.client
        return cli.execute_kw(
            'sale.order.line', 'read_group',
            [[
                ['order_id.date_order', '>=', from_date],
                ['state', 'in', ['sale', 'done']]  # 已确认，已完成
            ]],
            {
                'fields': ['product_id', 'product_uom_qty:sum'],
                'groupby': ['product_id']
            })

    # 生成产品销量报表
    def product_sales_report(self):
        cli = self.api.client
        # 时间范围
        today = datetime.datetime.today()
        date_30 = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        date_60 = (today - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
        date_90 = (today - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
        date_120 = (today - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
        date_150 = (today - datetime.timedelta(days=150)).strftime('%Y-%m-%d')
        date_180 = (today - datetime.timedelta(days=180)).strftime('%Y-%m-%d')

        # 获取销售数据
        sales_30 = self._get_sales_data(date_30)
        sales_60 = self._get_sales_data(date_60)
        sales_90 = self._get_sales_data(date_90)
        sales_120 = self._get_sales_data(date_120)
        sales_150 = self._get_sales_data(date_150)
        sales_180 = self._get_sales_data(date_180)

        sales_data = {}

        def merge_sales(data, key):
            for rec in data:
                if not rec['product_id']:
                    continue
                pid = rec['product_id'][0]
                if pid not in sales_data:
                    sales_data[pid] = {}
                sales_data[pid][key] = rec['product_uom_qty']

        merge_sales(sales_30, '30d')
        merge_sales(sales_60, '60d')
        merge_sales(sales_90, '90d')
        merge_sales(sales_120, '120d')
        merge_sales(sales_150, '150d')
        merge_sales(sales_180, '180d')

        # 只保留有销量的
        filtered_ids = [pid for pid, vals in sales_data.items() if any(vals.values())]

        # 查询产品基本信息
        products = cli.read(
            'product.product',
            [filtered_ids],
            {'fields': ['name', 'default_code', 'qty_available', 'virtual_available', 'product_tmpl_id']}
        )

        # 提取所有模板 ID
        tmpl_ids = list(set([p['product_tmpl_id'][0] for p in products]))

        supplier_infos = cli.search_read(
            'product.supplierinfo',
            [[['product_tmpl_id', 'in', tmpl_ids]]],
            {'fields': ['product_tmpl_id', 'delay', 'min_qty', 'product_uom', 'partner_id', ],
             'order': 'sequence asc'}
        )

        # 建立 tmpl_id → supplier_info 映射表（只取第一条）
        supplier_info_map = {}
        for info in supplier_infos:
            tmpl_id = info['product_tmpl_id'][0]
            if tmpl_id not in supplier_info_map:
                supplier_info_map[tmpl_id] = info  # 保存完整 supplier_info 字典

        # 组装表格数据
        rows = []
        for product in products:
            pid = product['id']
            tmpl_id = product['product_tmpl_id'][0]
            info = supplier_info_map.get(tmpl_id, {})
            vendor_lead_time = info.get('delay', 7)
            min_qty = info.get('min_qty', 1)
            sales30d = round(sales_data[pid].get('30d', 0), 2)
            sales60d = round(sales_data[pid].get('60d', 0), 2)
            sales90d = round(sales_data[pid].get('90d', 0), 2)
            sales120d = round(sales_data[pid].get('120d', 0), 2)
            sales150d = round(sales_data[pid].get('150d', 0), 2)
            sales180d = round(sales_data[pid].get('180d', 0), 2)
            qty_available = round(product.get('qty_available', 0), 2)
            if int(sales60d-sales30d) == 0:
                sales_growth_rate = 0
            else:
                sales_growth_rate = (sales30d - (sales60d-sales30d)) / (sales60d-sales30d)  # 最近销量增长率
                sales_growth_rate = round(sales_growth_rate, 2)

            row = {
                'SKU': product.get('default_code') or '',
                'Product Name': product['name'],
                'Sales (30d)': sales30d,
                'Sales (60d)': sales60d,
                'Sales (90d)': sales90d,
                'Sales (120d)': sales120d,
                'Sales (150d)': sales150d,
                'Sales (180d)': sales180d,
                'On-Hand Quantity': qty_available,
                'Forecasted Quantity': round(product.get('virtual_available', 0), 2),
                'Sell-Through Rate (30d)': round(sales30d / max(qty_available, 1), 2),
                "Sales Growth Rate": sales_growth_rate,
                'Vendor Lead Time (days)': max(vendor_lead_time, 1),
                'Vendor Min Qty': max(min_qty, 1),
                'UoM': info.get('product_uom', [None, ''])[1],
                'Supplier Name': info.get('partner_id', [None, ''])[1],
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.sort_values(by='SKU', ascending=True, inplace=True)
        # Rename
        df.rename(columns={
            'Product Name': '产品名称',
            "Sales (30d)": "30天销量",
            "Sales (60d)": "60天销量",
            "Sales (90d)": "90天销量",
            "Sales (120d)": "120天销量",
            "Sales (150d)": "150天销量",
            "Sales (180d)": "180天销量",
            "On-Hand Quantity": "在库数量",
            "Forecasted Quantity": "预测库存",
            "Sell-Through Rate (30d)": "30天动销比",
            "Sales Growth Rate": "30天销量增长率",
            "Vendor Lead Time (days)": "采购周期 (天)",
            "Vendor Min Qty": "起订量",
            "UoM": "单位",
            "Supplier Name": "供应商",
        },
            inplace=True
        )
        return df