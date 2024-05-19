import json
import os
import utils.stringutils as stringutils
import utils.winutils as winutils
from rest.amazon import Orders
from rest.gls import GlsShipment
# https://sellercentral.amazon.de/orders-v3/bulk-confirm-shipment/305-9644702-7230766;303-7790532-8849166;305-9644702-7230766;303-7790532-8849166

class AmazonBulkConfirmPipeline(object):

    def __init__(self, host):
        self.shipments = None
        self.ppath = os.path.join(os.getcwd(), "workspace")
        self.country = "DE"
        self.today = stringutils.today()
        self.subfolder = os.path.join(self.ppath, stringutils.today("%Y%m%d_%H%M%S"))
        self.base_url = f"{host}/api/v1/amazon"
        self.orderClient = Orders(self.base_url)
        self.glsClient = GlsShipment(f"{host}/api/v1/carriers")
        self.orderIds = None  # List of unshipped order ids
        self.shippedOrderIds = None  # List of shipped order ids
        self.bulkConfirmBaseUrl = None
        self.packSlipBaseUrl = None
        self.packSlipFilePath = None


    def process(self):
        self.initialize()
        self.receive_order()
        self.process_pack_slips()
        self.create_parcel_labels()
        self.confirm_orders()
        self.save_results()

    def initialize(self):
        # Initialize the pipeline
        data = self.orderClient.get_seller_central_urls()
        data = data['data']
        os.makedirs(self.subfolder, exist_ok=True)
        self.__append_to_history(f"Pipeline initialized on {self.today}\n")
        self.bulkConfirmBaseUrl = data['bulk-confirm-shipment']
        self.packSlipBaseUrl = data['packing-slip']

    def receive_order(self):
        # Receive unshipped orders from Amazon seller central
        res = self.orderClient.unshipped_order_ids()
        orderIds = res['data']
        if len(orderIds) == 0:
            raise RuntimeError("No unshipped orders found")
        string = stringutils.print_array_in_format(orderIds, 4)
        self.__append_to_history(string)
        self.orderIds = orderIds

        bulkPackSlipUrl = f"{self.packSlipBaseUrl}/?orderIds={';'.join(orderIds)}"
        self.__append_to_history(f"Bulk packing slip download URL: \n{bulkPackSlipUrl}\n")
        # winutils.show_message_box("Tips", "Please copy and past the URL in a browser to download packing slips.")
        packSlipFilePath = self.__create_pack_file(bulkPackSlipUrl)
        winutils.startfile(packSlipFilePath)
        self.packSlipFilePath = packSlipFilePath


    def process_pack_slips(self):
        # Process packing slips downloaded from Amazon seller central
        path = self.packSlipFilePath
        print(path)
        # path = r"F:\shared\test\shipping_slips_2024-05-19_135715.txt"
        winutils.show_message_box("Tips", f"Please paste the html content to {path}")
        input("Press any key to continue...")
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        res = self.orderClient.parsePackSlip(content=html, country=self.country)
        self.shipments = res['data']
        toprint = [f"{i+1:03d}. {ship['references'][0]}\t{ship['consignee']['country']}\t{ship['consignee']['street1']}"
                   for i, ship in enumerate(self.shipments)]
        self.__append_to_history("\nSuccessfully parsed packing slips:\n")
        self.__append_to_history("\n".join(toprint))
        winutils.show_message_box("Tips", f"\nSuccessfully parsed packing slips[{len(self.shipments)}]\n")

    def create_parcel_labels(self):
        # Create parcel labels for shipped orders
        self.__append_to_history("\nCreating parcel labels, please wait for a few minutes...\n")
        res = self.glsClient.bulk_create_shipments(self.shipments)
        toprint = [f"{i+1}. {ship['id']}\t{ship['status']}\t{ship['message']}" for i, ship in enumerate(res['data'])]
        self.__append_to_history("\nSuccessfully created parcel labels:\n")
        self.__append_to_history("\n".join(toprint))
        self.shippedOrderIds = [ship['id'] for i, ship in enumerate(res['data'])]
        # Filter out the unshipped orders
        self.shipments = list(filter(lambda x: ";".join(x['references']) in self.shippedOrderIds, self.shipments))

    def confirm_orders(self):
        # Confirm shipped orders on Amazon seller central
        pass

    def save_results(self):
        self.__append_to_history("\nPrint Results:\n")
        # Show bulk packing slip download URL
        packSlipUrl = f"{self.packSlipBaseUrl}/?orderIds={';'.join(self.shippedOrderIds)}"
        self.__append_to_history(f"\nPacking slip download: \n{packSlipUrl}\n")
        # Show bulk parcel labels download URL
        labelsUrl = f"{ self.glsClient.base_url}/bulk-labels?refs={';'.join(self.shippedOrderIds)}"
        self.__append_to_history(f"\nParcel labels download: \n{labelsUrl}\n")
        # TODO Show picking slip download URL
        pickSlipUrl = f"{self.glsClient.base_url}/report?refs={';'.join(self.shippedOrderIds)}"
        self.__append_to_history(f"\nPicking slip download: \n{pickSlipUrl}\n")

        # Show bulk confirm shipment URL
        bulkConfirmUrl = f"{self.bulkConfirmBaseUrl}/{';'.join(self.shippedOrderIds)}"
        self.__append_to_history(f"\nBulk confirm shipment: \n{bulkConfirmUrl}\n")


        # Save gls labels to a pdf file
        res = self.glsClient.get_bulk_ship_labels(self.shippedOrderIds)
        with open(os.path.join(self.subfolder, f"{self.__get_file_name()}.pdf"), "wb") as f:
            f.write(res)


        # Save Shipment
        data = dict(size=len(self.shipments), data=self.shipments)
        with open(os.path.join(self.subfolder, f"{self.__get_file_name()}.json"),
                  "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # TODO Save packing slips to a html file

        # TODO Save picking slips to a excel file
        data = self.glsClient.get_pick_pack_slip(self.shippedOrderIds)
        with open(os.path.join(self.subfolder, f"pick_pack_slips.xlsx"), "wb") as f:
            f.write(data)

        # Save TRACKID mapping to a txt file
        data = self.glsClient.get_pick_items(self.shippedOrderIds)
        data = data['data']
        trackIdMap = {item["orderId"]: item["trackId"] for item in data}
        # convert trackIdMap to a string
        trackIdMapStr = "\n".join([f"{k}: {v}" for k, v in trackIdMap.items()])
        with open(os.path.join(self.subfolder, f"track_ids.txt"), "w", encoding="utf-8") as f:
            f.write(bulkConfirmUrl + "\n\n\n")
            f.write(trackIdMapStr)
        winutils.copy_to_clipboard(trackIdMapStr)

        self.__append_to_history(f"\nSaved results to {self.subfolder}\n")
        winutils.startfile(self.subfolder)

    def __append_to_history(self, data: str):
        # Append data to a file
        print(data)
        with open(os.path.join(self.subfolder, "history.txt"), "a", encoding="utf-8") as f:
            f.write(data)
            f.write("\n")

    def __create_pack_file(self, bulkPackSlipUrl):
        bulkPackSlipUrl = f"view-source:{bulkPackSlipUrl}"
        # Create a file with packing slips
        fpath = os.path.join(self.subfolder, f"{self.__get_file_name()}.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            text = f"Please download packing slips from the following URL:\n\n{bulkPackSlipUrl}\n\n"
            text += "Just copy and paste the html content to overwrite the file and save it by ctrl+s.\n\n"
            f.write(text)
        return fpath

    def __get_file_name(self):
        wb = self.today.replace(":", "").replace(" ", "_")
        return f"shipping_slips_{wb}"
