from models.orders import StandardOrder, OrderItem
from models.shipment import StandardShipment

"""
Standardize the data from MongoDB
The module search data in a way of cross-collections in mongodb 
"""

def amazon_to_standard_order(shipment: dict, order: dict) -> StandardOrder:
    """
    This function converts the Amazon shipping slip page to a list of StandardOrder objects.
    :param shipment: shipment from MongoDB
    :param order: order from MongoDB
    :return:
    """
    standardShipment = StandardShipment.parse_obj(shipment['details'])
    numParcels = len(standardShipment.parcels)
    trackIds = [standardShipment.parcels[i].trackNumber for i in range(numParcels)]
    parcelNumbers = [standardShipment.parcels[i].parcelNumber for i in range(numParcels)]

    shipAddress = standardShipment.consignee
    billAddress = standardShipment.consignee

    orderId = order['_id']
    orderItems = order['items']['OrderItems']
    standardOrderItems = []
    for item in orderItems:
        quantity = int(item['QuantityOrdered'])
        unit_price = float(item['ItemPrice']['Amount'])
        tax = float(item['ItemTax']['Amount'])
        stdItem = OrderItem(id=item['ASIN'],
                            name=item['Title'],
                            sku=item['SellerSKU'],
                            quantity=quantity,
                            unit_price=unit_price,
                            subtotal=unit_price * quantity,
                            tax=tax,
                            total=unit_price * quantity + tax,
                            description="",
                            image="")
        standardOrderItems.append(stdItem)

    standardOrder = StandardOrder(orderId=orderId,
                                  sellerId=order['account_id'],
                                  salesChannel="SalesChannel",
                                  createdAt=order['order']['PurchaseDate'],
                                  updatedAt=order['order']['LastUpdateDate'],
                                  purchasedAt=order['order']['PurchaseDate'],
                                  status=order['order']['OrderStatus'],
                                  items=standardOrderItems,
                                  shipAddress=shipAddress,
                                  billAddress=billAddress,
                                  trackIds=trackIds,
                                  parcelNumbers=parcelNumbers)
    return standardOrder



def update_standard_order_with_amazon_order(standard_order: StandardOrder, amazon_order: dict):
    """
    TODO This function standardizes the order data from Amazon and updates the StandardOrder object.
    :param standard_order: StandardOrder object
    """
    pass

def update_standard_order_with_shipment(standard_order: StandardOrder, shipment: StandardShipment):
    """
    TODO This function standardizes the shipment data from Amazon and updates the StandardOrder object.
    :param standard_order: StandardOrder object
    :param shipment: shipment from MongoDB
    """
    pass