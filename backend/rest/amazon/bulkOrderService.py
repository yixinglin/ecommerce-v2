import re
from typing import List, Union
import bs4
import utils.city as city
import utils.time as util_time
import utils.translate as trans
from core.log import logger
from models.orders import StandardOrder, OrderItem
from models.shipment import Address


class AmazonBulkPackSlipDE:
    """
    This class is used to extract information from Amazon shipping slip page in German.
    The result of this class is a list of StandardShipment objects, which can be used for further processing.
    """

    def __init__(self, html: str):
        """
        Initialize the AmazonBulkPackSlipDE object with the HTML content of the shipping slip page.
        This function will parse the HTML content and extract all necessary information.
        Note: Only German shipping addresses are supported.
        :param html: The HTML content of the shipping slip page.
        """
        self.soup = bs4.BeautifulSoup(html, 'html.parser')

    def get_order_ids(self) -> List[str]:
        """
        This function extracts all order IDs from Amazon shipping slip page.
        :return:
        """
        order_ids = []
        for order in self.soup.select('div.myo-orderId'):
            order_id_str = order.text.strip()
            match = re.search(r'\d{3}-\d{7}-\d{7}', order_id_str)
            if match:
                id = match.group()
                order_ids.append(id)
            else:
                raise RuntimeError(f'Invalid order ID: {order_id_str}')
        return order_ids

    def get_shipping_addresses(self) -> list:
        """
        This function extracts all shipping addresses from Amazon shipping slip page.
        :return:  A list of shipping addresses in html format.
        """
        shipping_addresses = []  # list of shipping addresses in html format
        # for i, table in enumerate(self.soup.select("div.myo-mena-packing-slip span#myo-order-details-buyer-address")):
        for i, table in enumerate(self.soup.select(".myo-address #myo-order-details-buyer-address")):
            shipping_address = table.text.strip()
            shipping_address = list(filter(lambda x: x.strip() != "", shipping_address.split("\n")))
            shipping_address = [s.strip().replace(";", ",") for s in reversed(shipping_address)]
            if len(shipping_address) > 3:
                shipping_addresses.append(shipping_address)
        return shipping_addresses

    def adjust_shipping_address(self, shipping_address: List[str]) -> List[str]:
        """
        This function can only apply to a German shipping address
        :param shipping_address: The original shipping address
        :return:  The adjusted shipping address
            Format of the shipping address: country, city, state, zip, street, supplement(name3), name(name2), company(name1)
        """
        # Filtering countries except Germany (Avoid using Google Translate)
        if shipping_address[0] not in ["Deutschland", "Germany"]:
            raise RuntimeError(f"Only German addresses are supported. {shipping_address}")

        # Convert country name to ISO code
        try:
            country_details = city.country_name_details(shipping_address[0])
        except KeyError:
            translated_name = trans.translate(shipping_address[0])  # country name in English
            country_details = city.country_name_details_by_shortname(translated_name)

        if not country_details:
            raise RuntimeError(f"Unknown Country: {shipping_address}")

        country_code = country_details["alpha_2"]
        shipping_address[0] = country_code

        # Validate zip code format
        if city.valid_zip_code(shipping_address[2], country_code):
            shipping_address.insert(2, "")  # insert empty state if missing
        elif city.valid_zip_code(shipping_address[3], country_code):
            shipping_address[1], shipping_address[2] = shipping_address[2], shipping_address[1]

        # Filtering countries except Germany
        if country_code.lower() != "de":
            raise RuntimeError(f"Only German addresses are supported. {shipping_address}")

        # Filtering items included DHL, Packstation, Postfiliale
        keyword = ["dhl", "packstation", "postfiliale"]
        for kw in keyword:
            if kw in ";".join(shipping_address).lower():
                raise RuntimeError(f"Address included [{kw}] are not supported. {shipping_address}")
        # Filtering address without sufficient information
        if len(shipping_address) < 6:
            raise RuntimeError(f"Address information is missing. {shipping_address}")

        # Swap street and address supplement if necessary
        if not city.identify_german_street(shipping_address[4]):
            if city.identify_german_street(shipping_address[5]):
                shipping_address[4], shipping_address[5] = shipping_address[5], shipping_address[4]

        pattern = r"^\d+[a-zA-Z]?(?:[-\/]\d+[a-zA-Z]?)?$"
        # If customer wrongly wrote the street name with house number, try to fix it.
        if re.match(pattern, shipping_address[4]):  # if the street name is written with a house number
            shipping_address[4], shipping_address[5] = shipping_address[5], shipping_address[4]
            shipping_address[4] += " " + shipping_address[5]
            shipping_address[5] = "~"

        # Restrict the length of the list to 8
        if len(shipping_address) == 6:
            shipping_address.insert(5, "")
            shipping_address.insert(5, "")
        elif len(shipping_address) == 7:
            shipping_address.insert(5, "")

        # Check if the length of the list is 8
        if len(shipping_address) != 8:
            raise RuntimeError(f"Some error occurred while adjusting "
                               f"the shipping address (length). {shipping_address}, {len(shipping_address)} != 8")

        # Swap company name and personal name again if necessary
        if city.is_company_name(shipping_address[6]):
            shipping_address[6], shipping_address[7] = shipping_address[7], shipping_address[6]

        # Final validation
        if not city.identify_german_street(shipping_address[4]):
            raise RuntimeError(f"Invalid street name: {shipping_address[4]}")
        if not city.valid_zip_code(shipping_address[3]):
            raise RuntimeError(f"Invalid zip code: {shipping_address[3]}")

        # Todo Not a product needing a transparent code

        return shipping_address

    def get_order_items(self) -> list:
        """
        This function extracts all purchased items from an Amazon shipping slip page.
        :return:
        """
        order_items = []
        # find all tables with class 'table-border'
        for table in self.soup.select('table.table-border'):
            order_items.append(self.__get_table_details(table))
        return order_items

    def __get_table_details(self, table):
        """
        This function extracts the details of all items in a table
        :param table:
        :return:
        """
        trs = table.select('table.table-border > tr')
        collection_item_details = []
        del trs[0]
        for item in trs:
            tds = item.find_all('td')
            quantity = int(tds[0].text.strip())
            title = tds[1].select_one('td > span').text.strip()
            spans = tds[1].select('td > div > span')
            sku = spans[1].text.strip()
            asin = spans[3].text.strip()
            unitPrice = tds[2].text
            collection_item_details.append({
                'quantity': quantity,
                'title': title,
                'sku': sku,
                'asin': asin,
                'unitPrice': unitPrice
            })
        return collection_item_details

    def extract_all(self, format=None) -> Union[List[StandardOrder], List[tuple], List[dict]]:
        """
        This function extracts all necessary information from Amazon shipping slip page.
        :param format: output format, e.g. json, csv. Default is a list of StandardShipment objects.
        :return: A list of shipping addresses in the specified format.
        """
        ids = self.get_order_ids()
        items = self.get_order_items()
        addresses = self.get_shipping_addresses()
        ans = []
        for i in range(len(ids)):
            try:
                adjusted_addr = self.adjust_shipping_address(addresses[i])
                id = ids[i]
                item = items[i]
                # shipment = self.to_standard_shipment(id, item, adjusted_addr)
                standardOrder = self.to_standard_order(id, item, adjusted_addr)
                if format == 'json':
                    ans.append(standardOrder.dict())
                elif format == 'csv':
                    ans.append([id, util_time.now()] + adjusted_addr)
                else:
                    ans.append(standardOrder)
            except (RuntimeError, KeyError) as e:
                    logger.error(f"Error while adjusting shipping address: {e}"
                             + ";".join(addresses[i]))
        return ans


    def to_standard_order(self, orderId, items, address) -> StandardOrder:
        """
        This function converts the Amazon shipping slip page to a StandardOrder objects.
        :param orderId:
        :param items:
        :param address:
        :return:
        """
        consignee = Address(
            country=address[0],
            city=address[1],
            province=address[2],
            zipCode=address[3],
            street1=address[4],
            name3=address[5],
            name2=address[6],
            name1=address[7]
        )

        orderlines = []
        for i, item in enumerate(items):
            orderline = OrderItem(
                id = f"slipid_{i}",
                name=item['title'],
                sku=item['sku'],
                asin=item['asin'],
                quantity=item['quantity'],
            )
            orderlines.append(orderline)

        order = StandardOrder(
            orderId=orderId,
            shipAddress=consignee,
            items=orderlines
        )

        return order