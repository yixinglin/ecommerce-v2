
class ShipmentExistsException(RuntimeError):
    def __init__(self, message):
        super().__init__(message)

class DimensionNotFoundException(RuntimeError):
    def __init__(self, message):
        super().__init__(message)

