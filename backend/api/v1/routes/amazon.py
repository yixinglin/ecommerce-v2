import os
from typing import Any, List, Union
from fastapi import APIRouter, Request, Response, Query, Body, Path
from sp_api.base import Marketplaces

from core.log import logger
from models.orders import StandardOrder
from rest.amazon.base import AmazonSpAPIKey
from rest.amazon.bulkOrderService import AmazonBulkPackSlipDE
from schemas import ResponseSuccess
from rest import AmazonOrderMongoDBManager, AmazonCatalogManager
from core.config import settings
from schemas.basic import BasicResponse
from vo.amazon import DailyShipment, DailySalesCountVO, PackSlipRequestBody
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

amz_order = APIRouter(tags=['AMAZON Services'])


def get_asin_image_url_dict(marketplace: Marketplaces) -> dict:
    with AmazonCatalogManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                              key_index=0, marketplace=marketplace) as man:
        catalogItems = man.get_all_catalog_items()
    result = dict()
    for catalogItem in catalogItems:
        try:
            result[catalogItem['_id']] = catalogItem['catalogItem']['AttributeSets'][0]['SmallImage']['URL']
        except KeyError as e:
            logger.error(f"Error while getting ASIN image URL for {catalogItem['_id']}")
    return result


@amz_order.get("/orders/ordered-items-count/daily/{days_ago}",
               summary="Get daily ordered items count",
               response_model=BasicResponse[List[DailySalesCountVO]])
def get_daily_ordered_items_count(response: Response,
                                  days_ago: int = Path(description="Fetch data for the last x days"),
                                  country: str = Query("DE", description="Marketplace ")) -> Any:
    marketplace = AmazonSpAPIKey.name_to_marketplace(country)
    with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=0, marketplace=marketplace) as man:
        daily = man.get_daily_mfn_sales(days_ago=days_ago)

    # Convert daily-sales data to DailySalesCountVO objects
    daily_sales_vo = []
    for day in daily:
        # Convert dailyShipments JSON array to list of DailyShipment objects
        daily_shipments = [DailyShipment(**item) for item in day['dailyShipments']]
        # Create DailySalesCountVO object
        vo = DailySalesCountVO(purchaseDate=day['purchaseDate'],
                               hasUnshippedOrderItems=day['dailyShippedItemsCount'] < day['dailyOrdersItemsCount'],
                               dailyShippedItemsCount=day['dailyShippedItemsCount'],
                               dailyOrdersItemsCount=day['dailyOrdersItemsCount'],
                               dailyShipments=daily_shipments)
        daily_sales_vo.append(vo)

    asin_image_url = get_asin_image_url_dict(marketplace)
    for day in daily_sales_vo:
        for shipment in day.dailyShipments:
            shipment.imageUrl = asin_image_url.get(shipment.asin, "")
    return ResponseSuccess(data=daily_sales_vo, )


# Show daily ordered items count using html template
@amz_order.get("/orders/ordered-items-count/daily/{days_ago}/treeview",
               summary="Get daily ordered items count in html format",
               response_class=HTMLResponse, )
def view_daily_ordered_items_count_html(request: Request, response: Response,
                                        days_ago: int=Path(description="Fetch data for the last x days"),
                                        country: str=Query("DE", description="Marketplace to use (DE, UK, US"),) -> Any:
    data = get_daily_ordered_items_count(days_ago=days_ago, response=response, country=country)
    templates = Jinja2Templates(directory=os.path.join("assets", "templates", "web"))
    return templates.TemplateResponse(name="AmazonDailySalesCount.html",
                                      request=request,
                                      headers={"Cache-Control": "max-age=3600, public"},
                                      context={"data": data.data})


@amz_order.get("/orders/unshipped",
               summary="Get unshipped order numbers",
               response_model=BasicResponse[List[str]])
def get_unshipped_order_numbers(country: str=Query("DE", description="Country of the marketplace")) -> List[str]:
    """
    Get Amazon order numbers that have unshipped items. The order numbers are sorted by sku.
    :country: Country code that is used to determine a marketplace.
    :return:  List of Amazon order numbers that have unshipped items

    """
    marketplace = AmazonSpAPIKey.name_to_marketplace(country)
    with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=0, marketplace=marketplace) as man:
        unshipped_orders = man.find_unshipped_order(days_ago=7)
        order_numbers = [order.orderId for order in unshipped_orders]
        return ResponseSuccess(data=order_numbers)

@amz_order.get("/orders/sc-urls",
               summary="Get seller central urls",
               response_model=BasicResponse[dict])
def get_seller_central_urls():
    urls = {
        "bulk-confirm-shipment": "https://sellercentral.amazon.de/orders-v3/bulk-confirm-shipment",
        "packing-slip": "https://sellercentral.amazon.de/orders/packing-slip"
    }
    return ResponseSuccess(data=urls)



@amz_order.post("/orders/packslip/parse",
               summary="Parse Amazon packing slip and extract all shipments.",
               response_model=BasicResponse[Union[List[StandardOrder], List[List[str]]]])
def parse_amazon_pack_slip_html(body: PackSlipRequestBody=Body(None, description="Packing slip data")):
    """
    Parse Amazon packing slip and extract all shipping addresses, store it to MongoDB.
    :param html:
    :param country: Country code using to filtering the packing slips
    :param format: csv, json
    :return: A list of StandardOrder objects.
    """
    formatIn = body.formatIn
    format_ = body.formatOut
    country = body.country
    html_content = body.data

    # html_content = requests.get("https://www.hamster25.buzz/amazon/amazon-delivery-de-03.html").content
    marketplace = AmazonSpAPIKey.name_to_marketplace(country)
    # Result to return
    if country == "DE":
        # Result to return
        orders = AmazonBulkPackSlipDE(html_content).extract_all(format=format_)
        # Update shipping address to MongoDB
        orders_: StandardOrder = AmazonBulkPackSlipDE(html_content).extract_all()
        with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                       key_index=0, marketplace=marketplace) as man:
            for order_ in orders_:
                man.add_shipping_address_to_order(order_.orderId, order_.shipAddress)
    else:
        raise RuntimeError(f"Unsupported marketplace [{country}]")
    return ResponseSuccess(data=orders)

