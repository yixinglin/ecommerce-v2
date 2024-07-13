from models.orders import StandardOrder
from models.shipment import StandardShipment, Parcel, Address
from utils.stringutils import isEmpty


def convert_to_standard_shipment(order: StandardOrder,
                                 carrier: str):
    consignee: Address = order.shipAddress
    if consignee is None or isEmpty(consignee.name1) \
            or isEmpty(consignee.street1) or isEmpty(consignee.country) \
            or isEmpty(consignee.zipCode) or isEmpty(consignee.city):
        raise RuntimeError("Consignee address is missing or incomplete")
    content = ""
    for item in order.items:
        content += f"{item.quantity} x [{item.sku}]\n"
    parcel = Parcel.default()
    parcel.content = content.strip()
    shipment = StandardShipment(carrier=carrier,
                                consignee=consignee,
                                parcels=[parcel],
                                references=[order.orderId],
                                )
    return shipment
