import datetime

from schemas.common import UTCModel


class BatchInformation(UTCModel):
    batch_id: str
    listing_id: str
    seller_sku: str
    created_at: datetime.datetime
    hash: str
    filename: str
    total: int
    used: int
    locked: int
    deleted: int

class OverallStatistics(UTCModel):
    total: int
    unused: int
    used: int
    locked: int
    deleted: int

class SkuStatistics(UTCModel):
    seller_sku: str
    listing_id: str
    unused: int
    history_used: int
    history_total: int
