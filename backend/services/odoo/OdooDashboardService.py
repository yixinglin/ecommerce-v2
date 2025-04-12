import datetime
from typing import List

import numpy as np
import pandas as pd
import plotly.express as px
from services.odoo.OdooOrderService import OdooOrderService

class OdooOrderDashboardService:

    def __init__(self, key_index, login=True, *args, **kwargs):
        self.key_index = key_index
        self.svc_order = OdooOrderService(key_index, login=login)
        self.api = self.svc_order.api

    def __enter__(self):
        self.svc_order.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.svc_order.__exit__(exc_type, exc_val, exc_tb)

    def stats_sales_order_by_salesman(self, salesman_ids: List[int] = None, days_ago: int = 365):
        orderlines_data = self.svc_order.query_orderlines_by_salesman_id(salesman_ids)
        df_sale_order_lines = self.to_sales_orderlines_dataframe(orderlines_data, days_ago)

        # 获得所有订单产品
        product_ids = [line[1]['product_id'] for line in df_sale_order_lines.iterrows()]
        product_ids = list(set(product_ids))
        products_data = self.svc_order.svc_product.query_product_templates_by_ids(product_ids)
        df_products = pd.DataFrame.from_dict(
            [d.dict() for d in products_data],
        )
        df_products['id'] = df_products['id'].astype(int)
        df_exact = df_sale_order_lines.merge(
            df_products[["id", "name", 'sku', "code", "price", "weight", "uom", "cost", "barcode"]], \
            left_on='product_id', right_on='id', how="left")

        df_sales_orderlines_combined = df_exact.copy()
        df_sales_orderlines_combined.loc[
            df_sales_orderlines_combined['product_name'] == 'Versandkostenpauschale', 'price'] = 0

        df_sales_orderlines_combined['total_weight'] = df_sales_orderlines_combined['product_uom_qty'] * \
                                                       df_sales_orderlines_combined['weight']
        df_sales_orderlines_combined['order_cost'] = df_sales_orderlines_combined['product_uom_qty'] * \
                                                     df_sales_orderlines_combined['cost']

        # 按订单号聚合订单明细.
        df_agg_orderlines = df_sales_orderlines_combined.groupby('order_number') \
            .agg({'create_date': 'first', 'product_name': 'nunique',
                  'order_partner': 'first', 'salesman': 'first', 'total_weight': 'sum',
                  'price_tax': 'sum', 'price_subtotal': 'sum', 'order_cost': 'sum', 'currency': 'first'}) \
            .rename(columns={'product_name': 'line_count'}) \
            .reset_index()

        df_agg_orderlines['estimated_shipping_cost'] = 9.99
        df_agg_orderlines['estimated_profit'] = df_agg_orderlines['price_subtotal'] - df_agg_orderlines['order_cost'] - \
                                                df_agg_orderlines['estimated_shipping_cost']

        sales_order_combined = df_agg_orderlines.copy()

        return sales_order_combined



    def to_sales_orderlines_dataframe(self, orderlines_data, days_ago: int = 365):
        df_sale_order_lines = pd.DataFrame.from_dict(
             [ d.dict() for d in orderlines_data ],
        )
        df_sale_order_lines['create_date'] = pd.to_datetime(
            df_sale_order_lines['create_date'],
            format='%Y-%m-%d %H:%M:%S')

        # 数据清洗
        # 被取消的orderlines
        df_filtered_orderlines = df_sale_order_lines[df_sale_order_lines['state'] == 'sale']
        # 过去n天内的订单
        today = datetime.datetime.now()
        past_days = today - datetime.timedelta(days=days_ago)

        df_sale_order_lines.sort_values(by='create_date', inplace=True)
        df_filtered_orderlines = df_filtered_orderlines[df_filtered_orderlines['create_date'] >= past_days]


        qty_to_invoice_zero = 1
        qty_to_deliver_zero = 1
        product_type = df_filtered_orderlines['product_type'] != 'product'
        df_filtered_orderlines = df_filtered_orderlines[qty_to_invoice_zero & (qty_to_deliver_zero | product_type)]
        df_filtered_orderlines = df_filtered_orderlines[df_filtered_orderlines['price_unit'] != 0]

        # Create month, year columns, 2024-07-25 10:46:01 to 2024-07
        df_filtered_orderlines['year'] = df_filtered_orderlines['create_date'].dt.strftime('%Y')
        df_filtered_orderlines['month'] = df_filtered_orderlines['create_date'].dt.strftime('%Y-%m')

        return df_filtered_orderlines

    def __classify_customer(self, row):
        """
        Classify customers into different types based on their RFM scores.
        """
        # 高价值客户: 忠诚度评分较高，购买金额、频率较高，且最近购买时间较短。
        if row['loyalty_score'] >= 4.0:
            return 'High-Value Customers'
        # 潜在流失客户: 最近购买时间较久，频率较高，曾经是重要客户，但可能流失。
        elif row['recency_score'] in [1, 2] and row['frequency_score'] >= 4 and row['monetary_score'] >= 4:
            return 'At-Risk Customers'
        # 新客户: 最近购买时间短，但购买频率和金额较低。
        elif row['recency_score'] >= 4 and row['frequency_score'] <= 2 and row['monetary_score'] <= 2:
            return 'New Customers'
        # 其他客户
        else:
            return 'Others'

    def stats_sales_order_by_customer(self, days_ago: int = 365):
        orderlines_data = self.svc_order.query_orderlines_by_salesman_id(salesman_ids=None)
        df_sale_order_lines = self.to_sales_orderlines_dataframe(orderlines_data, days_ago)
        reference_date = pd.Timestamp.now()
        # 统计每一个客户的销售额 (不含运费，不含未结的)
        df_customer_sales = df_sale_order_lines.groupby('order_partner') \
            .agg({'price_subtotal': "sum", 'currency': 'first', 'order_number': 'nunique'})

        df_customer_sales = df_customer_sales.rename(columns={'order_number': 'order_count'})

        df_customer_sales = df_customer_sales.sort_values('price_subtotal', ascending=False)
        df_customer_sales['avg_order_price'] = df_customer_sales['price_subtotal'] / df_customer_sales['order_count']
        df_customer_sales['avg_order_price'] = df_customer_sales['avg_order_price'].round(2)

        # 距离上次购买时间 (天)
        last_order_days = df_sale_order_lines.groupby('order_partner')['create_date'].max().reset_index()
        last_order_days['last_order_days'] = (reference_date - last_order_days['create_date']).dt.days
        df_customer_sales = pd.merge(df_customer_sales, last_order_days[['order_partner', 'last_order_days']],
                                     on='order_partner', how='left')

        # 订单金额评分
        df_customer_sales['monetary_score'] = pd.qcut(df_customer_sales['price_subtotal'], 5, labels=[1, 2, 3, 4, 5])
        # 订单次数评分
        df_customer_sales['noisy_order_count'] = df_customer_sales['order_count'] + np.random.uniform(0, 0.01, size=len(
            df_customer_sales))
        df_customer_sales['frequency_score'] = pd.qcut(df_customer_sales['noisy_order_count'], 5,
                                                       labels=[1, 2, 3, 4, 5])
        # 回购评分
        df_customer_sales['recency_score'] = pd.qcut(df_customer_sales['last_order_days'], 5, labels=[5, 4, 3, 2, 1])

        df_customer_sales.drop(columns=['noisy_order_count'], inplace=True)

        # 忠诚度得分：综合 RFM 评分（可加权）
        df_customer_sales['loyalty_score'] = df_customer_sales['recency_score'].astype(int) + \
                                             df_customer_sales['frequency_score'].astype(int) + \
                                             df_customer_sales['monetary_score'].astype(int)
        df_customer_sales['loyalty_score'] = df_customer_sales['loyalty_score'] / 3
        df_customer_sales['loyalty_score'] = df_customer_sales['loyalty_score'].round(1)

        # 客户类型分类
        df_customer_sales['tag'] = df_customer_sales.apply(self.__classify_customer, axis=1)
        return df_customer_sales


    def stats_sales_order_by_customer_bubble_chart(self, days_ago: int = 365):
        df_customer_sales2 = self.stats_sales_order_by_customer(days_ago)
        # 准备数据
        df_customer_sales2['size'] = df_customer_sales2['order_count'] * 100  # 点的大小
        df_customer_sales2['label'] = df_customer_sales2['order_partner']  # 索引标签

        # 使用 Plotly 创建交互式散点图
        fig = px.scatter(
            df_customer_sales2,
            x='price_subtotal',  # 横坐标
            y='last_order_days',  # 纵坐标
            size='size',  # 点的大小
            color='order_count',  # 颜色映射
            hover_name='label',  # 鼠标悬停显示的内容
            hover_data={  # 添加其他悬停数据
                'avg_order_price': True,  # 显示 avg_order_price
                'order_count': ':.0f',  # 格式化 order_count 为整数
                'size': False,  # 不显示 size
                'tag': True  # 显示 tag
            },
            labels={
                'price_subtotal': 'Gesamt Netto (EUR)',
                'order_count': 'Auftragsmenge',
                'avg_order_price': 'Durchschn. Auftragswert (EUR)',
                'last_order_days': 'Zuletzete Bestelltage',
                'tag': "Klasse"
            },
            title=f"Statistik zu Kundenbestellungen"
        )

        anno = f"Datenquelle: Odoo"
        anno += f"<br>Zeitraum: Letzte {days_ago} Tage"
        anno += f"<br>Anzahl Kunden: {len(df_customer_sales2)}"
        anno += f"<br>Anzahl Aufträge: {df_customer_sales2['order_count'].sum()}"
        anno += f"<br>Gesamtumsatz: {df_customer_sales2['price_subtotal'].sum():.2f} EUR"

        # 设置布局
        fig.update_layout(
            xaxis_title="Gesamtumsatz - Netto (EUR)",
            yaxis_title="Zuletzete Bestelltage",
            coloraxis_colorbar=dict(title="Auftragsmenge"),
            template="plotly_white",
            width=1380,  # 图表的宽度（像素）
            height=500,  # 图表的高度（像素）
            annotations=[
                dict(
                    text=anno,
                    align="left",
                    showarrow=False,
                    xref="paper",  # 相对于图表的水平位置 (paper 表示相对整个图表区域)
                    yref="paper",  # 相对于图表的垂直位置
                    x=0.7,  # 靠近图表左侧
                    y=0.9,  # 图表下方的适当位置（负值表示在图表下方）
                    xanchor='left',  # 文本水平对齐方式
                    yanchor='bottom',  # 文本垂直对齐方式
                    font=dict(size=12, color="gray")  # 字体大小和颜色
                )
            ]
        )

        # 修改 y 轴刻度
        fig.update_yaxes(
            tickvals=list(range(0, 300, 30))  # 设置刻度为 0, 30, 60, ..., 最大值可根据数据范围调整
        )

        return fig.to_html(full_html=True)




