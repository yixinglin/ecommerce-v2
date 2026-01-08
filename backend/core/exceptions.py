from core.response2 import ErrorCode


class BusinessException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str = None
    ):
        self.code = code
        self.message = message or code.name


def raise_business_error(code: ErrorCode, msg: str = None):
    raise BusinessException(code, msg)

class ShipmentExistsException(RuntimeError):
    def __init__(self, message):
        super().__init__(message)

class DimensionNotFoundException(RuntimeError):
    def __init__(self, message):
        super().__init__(message)

