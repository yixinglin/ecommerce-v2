from typing import List
from pydantic import BaseModel, Field

class BatchOrderConfirmEvent(BaseModel):
    createdAt: str
    taskId: str
    batchId: str
    orderIds: List[str]
    shipmentIds: List[str]
    username: str = Field(default="Anonymous")
    message: str = Field(default="")
    parcelLabelB64: str = Field(default="", description="Base64 encoded PDF label")
    packSlipB64: str = Field(default="", description="Base64 encoded PDF pack slip")
    # orders: List[StandardOrder]
    # shipments: List[StandardShipment]
    printed: bool = Field(default=False)
    confirmed: bool = Field(default=False)




