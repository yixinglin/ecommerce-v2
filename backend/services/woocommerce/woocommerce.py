from datetime import datetime, timedelta
from typing import List, Dict

from fastapi import HTTPException

from core.log import logger
from crud.woocommerce import AsyncWoocommerceOrderDB
from external.woocommerce.extent import OrderClient
from external.woocommerce.wpapi import WooClient, ApiKey
import utils.time as time_utils
from models.woocommerce import OrderModel, parse_order
import pandas as pd

class OrderService:

    def __init__(self, key_index: ApiKey):
        self.mdb_order = AsyncWoocommerceOrderDB()
        self.key_index = key_index
        if self.key_index is not None:
            self.key = ApiKey.from_json(key_index)
            self.order_client = OrderClient(self.key)

    async def __aenter__(self):
        await self.mdb_order.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mdb_order.__aexit__(exc_type, exc_val, exc_tb)


    async def save_orders(self, days_ago=7):
        after_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
        params = {
            "after": after_date,
            "per_page": 100,  # 100 maximal allowed by API
            "orderby": "date",
            "order": "desc",
            "page": 1  # Start from the first page
        }

        all_orders = []

        while True:
            logger.info(f"Fetching orders after {after_date}, page {params['page']}...")
            data = self.order_client.fetch_orders(params=params)

            # if res.status_code != 200:
            #     print("Failed to fetch orders:", res.status_code, res.text)
            #     break

            orders = data['data']

            if not orders:  # No more orders to fetch
                break

            all_orders.extend(orders)
            logger.info(f"Fetched {len(orders)} orders.")
            params["page"] += 1  # Next page
        logger.info(f"Fetched {len(all_orders)} orders.")

        if all_orders:
            await self.__save_orders_to_mongodb(all_orders)
            logger.info(f"Saved {len(all_orders)} orders to database.")
        else:
            logger.info("No orders to save.")

    async def __save_orders_to_mongodb(self, orders: List[dict]):
        logger.info(f"Fetched {len(orders)} orders.")
        documents = [{
            "_id": order['id'],
            "fetchedAt": time_utils.now(),
            "data": order,
            "alias": self.key.name,
        }
            for order in orders
        ]
        count = await self.mdb_order.bulk_save_orders(documents)
        logger.info(f"Saved {count} orders to database.")
        return count

    async def find_orders(self, offset=0, limit=10, *args, **kwargs) -> List[Dict]:
        # 构建查询条件
        query = {}
        if "status" in kwargs and kwargs["status"]:
            query["data.status"] = kwargs["status"]

        results = await self.mdb_order.query_orders(
            offset=offset,
            limit=limit,
            filter=query,
        )
        return {
            "data": [parse_order(order['data']) for order in results['data']],
            "total": results['total'],
        }

    async def stat_ordered_sku(self, days_ago=7) -> Dict:
        after_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
        query = {
            "data.date_created": {
                "$gte": after_date
            }
        }
        results = await self.mdb_order.query_orders(
            filter=query, limit=10000,
        )

        data = [parse_order(order['data']) for order in results['data']]
        if not data:
            raise HTTPException(status_code=404, detail="No orders found.")

        records = []
        for order in data:
            for item in order.line_items:
                records.append({
                    "date_created": order.date_created,
                    "status": order.status,
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "product_name": item.name,
                })

        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df["date_created"]).dt.date
        grouped = (
            df.groupby(["date", "status", "sku", "product_name"], as_index=False)["quantity"]
            .sum()
        )
        # 4. 按 SKU 排序
        df_result = grouped.sort_values(by=["date", "status"], ascending=False)
        return df_result

