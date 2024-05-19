import io
from typing import List
import pandas as pd
from openpyxl.styles import Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.workbook import Workbook
from rest.common.standardize import *
from vo.carriers import PickSlipItemVO
from core.db import MongoDBDataManager
import utils.time as time_utils


class PickPackDataManager(MongoDBDataManager):

    def __init__(self, db_host, db_port):
        super().__init__(db_host, db_port)
        self.db_amazon_data = "amazon_data"
        self.db_carrier = "carrier"
        self.collection_orders = "orders"
        self.collection_catalog = "catalog"
        self.collection_shipments = "shipments"

    def get_orders_by_id(self, ids: List[str]):
        orders = []
        mdb_orders_coll = self.db_client[self.db_amazon_data][self.collection_orders]
        o = list(mdb_orders_coll.find({"_id": {"$in": ids}}))
        orders.extend(o)
        return orders

    def get_catalog_by_id(self, ids: List[str]):
        catalog = []
        mdb_catalog_coll = self.db_client[self.db_amazon_data][self.collection_catalog]
        c = list(mdb_catalog_coll.find({"_id": {"$in": ids}}))
        catalog.extend(c)
        return catalog

    def get_shipments_by_id(self, ids: List[str]):
        shipments_coll = self.db_client[self.db_carrier][self.collection_shipments]
        shipments = list(shipments_coll.find({"_id": {"$in": ids}}))
        return shipments

    def get_pick_slip_items(self, ids: List[str]) -> List[PickSlipItemVO]:
        """
        Get pick slip summary by order ids
        :param ids:  List of order ids.
        :return:  List of PickSlipItemVO.
        """
        orders = self.get_orders_by_id(ids)
        shipments = self.get_shipments_by_id(ids)
        map_orders = {o['_id']: o for o in orders}
        map_shipments = {s['_id']: s for s in shipments}
        if len(ids) != len(map_orders.keys()):
            raise RuntimeError("Duplicate order id found in the input list.")

        pick_slips = []
        orderedItems: List[OrderItem] = []

        for id in ids:
            order = map_orders[id]
            shipment = map_shipments[id]
            standard_order = amazon_to_standard_order(shipment, order)
            items = standard_order.items
            orderedItems.extend(items)
            for item in items:
                addr = standard_order.shipAddress
                pick_slip_item = PickSlipItemVO(
                    date=time_utils.now(),
                    carrier=shipment['carrier'],
                    orderId=id,
                    trackId=";".join(standard_order.trackIds),
                    parcelNumber=";".join(standard_order.parcelNumbers),
                    sku=item.sku,
                    title=item.name,
                    quantity=item.quantity,
                    storageLocation="",
                    imageUrl="",
                    street1=addr.street1, )
                pick_slips.append(PickSlipItemVO.parse_obj(pick_slip_item))

        itemIds = list(set([item.id for item in orderedItems]))
        map_catalog = self.get_catalog_by_id(itemIds)
        # TODO: Get image url from catalog. Currently, it is empty because the catalog data is not standardized.
        # for id in itemIds:
        #     cat = map_catalog[id]
        #     img_url = cat['catalogItem']['AttributeSets']['']
        return pick_slips

    def pick_slip_to_excel(self, pick_slips: List[PickSlipItemVO]) -> bytes:
        """
        Convert pick slip to Excel file.
        :param pick_slips:  List of PickSlipItemVO.
        :return:  Excel file in bytes.
        """
        df = pd.DataFrame([o.dict() for o in pick_slips])
        # Create a new workbook and worksheet
        wb = Workbook()
        ws = wb.active
        # Set column width
        ws.column_dimensions['A'].width = 21
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 4
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 8

        # Set headers
        headers = ["OrderID", "Sku", "StorageLocation", "Qty", "Street", "TrackID", "Carrier"]
        ws.append(headers)
        # Group by order id
        grouped = df.groupby('orderId', sort=False)

        for order_id, group in grouped:
            # Extract order basic information
            date = group['date'].iloc[0]
            carrier = group['carrier'].iloc[0]
            track_id = group['trackId'].iloc[0]
            street = group['street1'].iloc[0]
            # Extract order item information
            items = group[['sku', 'storageLocation', 'quantity']]

            # Add order item information to the table
            for i, r in enumerate(dataframe_to_rows(items, index=False, header=False)):
                sku, storage_location, quantity = r
                if i == 0:
                    ws.append([order_id, sku, storage_location, quantity, street, track_id, carrier])
                else:
                    ws.append(["", sku, storage_location, quantity, "", "", ""])

        # Count the quantity of each SKU
        sku_info = df.groupby('sku').agg({'quantity': 'sum', 'storageLocation': 'first'})
        # Sort by quantity
        sorted_sku_info = sku_info.sort_values(by='sku', ascending=True)
        # Write SKU count information to the table
        ws.append([""])
        ws.append([""])
        ws.append(["SKU", "Count", "Storage Location"])
        for sku, info in sorted_sku_info.iterrows():
            ws.append([sku,  info['quantity'], info['storageLocation']])
        ws.append([""])
        ws.append([""])
        ws.append(["Date", date])

        # Set alignment
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrapText=True)

        # Save the workbook to a file-like object
        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

