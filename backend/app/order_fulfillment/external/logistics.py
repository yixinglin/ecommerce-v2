from typing import Optional
import utils.auth as auth
from .clients import GlsEuApiClient
from ..common.enums import CarrierCode, AddressType
from ..interfaces import (
    ILogisticsProvider, Order
)
from ..models import IntegrationCredentialModel, AddressModel, ShippingLabelModel, ShippingLabelModel_Pydantic
from core.log import logger
from ..common.builders import build_gls_delivery_from_address, build_gls_single_parcel
from utils.stringutils import jsonpath


class DHLProvider(ILogisticsProvider):
    def __init__(self):
        self.credential: Optional[IntegrationCredentialModel] = None

    def set_credential(self, cred: IntegrationCredentialModel):
        self.credential = cred

    def get_carrier_code(self) -> str:
        return CarrierCode.DHL

    async def create_shipping_label(self, order: Order) -> ShippingLabelModel_Pydantic:
        """
        Create a DHL shipping label via Germany / Deutsche Post DHL API.
        """
        if not self.credential:
            raise Exception("DHL credential not set")

        raise NotImplementedError()


class GlsEuProvider(ILogisticsProvider):

    MAX_NAME_LENGTH = 37

    def __init__(self):
        self.credential: Optional[IntegrationCredentialModel] = None
        self.headers = {
            # "Host": "api.gls-group.eu",  # TODO: 生产的时候取消注释
            "Accept-Language": "en",
            "Accept-Encoding": "gzip,deflate",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic auth"
        }

    def set_credential(self, cred: IntegrationCredentialModel):
        self.credential = cred
        self.auth = auth.basic_auth(cred.api_key, cred.api_secret)
        self.headers["Authorization"] = self.auth


    def get_carrier_code(self) -> str:
        return CarrierCode.GLS_EU

    async def create_shipping_label(self, order: Order) -> ShippingLabelModel_Pydantic:
        """
        Create a GLS shipping label via Germany / Deutsche Post GLS API.
        """
        if not self.credential:
            raise Exception("GLS credential not set")

        # 从 credential.meta 中获取 base_url、账户号等配置
        base_url = self.credential.meta.get("base_url")
        shipper_id = self.credential.meta.get("shipper_id")
        shipping_address = await AddressModel.get(
            id=order.shipping_address_id,
            address_type=AddressType.SHIPPING
        )
        delivery_dict = build_gls_delivery_from_address(
            shipping_address
        )
        body = {
            "shipperId": shipper_id,
            "references": [order.order_number],
            "addresses": {
                "delivery": delivery_dict
            },
            "parcels": [
                build_gls_single_parcel(weight=1.0, comment="")
            ]
        }

        client = GlsEuApiClient(base_url, self.headers)
        data = await client.create_shipment(body)

        parcel_numbers = jsonpath(data, '$.parcels[*].parcelNumber')
        track_ids = jsonpath(data, '$.parcels[*].trackId')
        # locations = jsonpath(data, '$.parcels[*].location')

        location = data['location']
        label_file_base64 = data['labels'][0]

        lab = await ShippingLabelModel.create(
            tracking_number=",".join(track_ids),
            tracking_id=",".join(parcel_numbers),
            label_file_base64=label_file_base64,
            carrier_code=CarrierCode.GLS_EU,
            tracking_url=location,
            order_id=order.id,
            channel=order.channel,
            external_id=self.credential.external_id
        )
        return await ShippingLabelModel_Pydantic.from_tortoise_orm(lab)
