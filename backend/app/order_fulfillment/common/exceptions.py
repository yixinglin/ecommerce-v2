class OrderFulfillmentException(Exception):
    pass


class TrackingInfoSyncError(OrderFulfillmentException):
    pass

class ShippingLabelCreationError(OrderFulfillmentException):
    pass

class ShipmentRouteError(OrderFulfillmentException):
    pass