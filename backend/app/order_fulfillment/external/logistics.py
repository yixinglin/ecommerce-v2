import re
from typing import Optional
import utils.auth as auth
from .clients import GlsEuApiClient
from ..common.enums import CarrierCode, AddressType
from ..common.exceptions import ShipmentRouteError
from ..interfaces import (
    ILogisticsProvider, Order
)
from ..models import IntegrationCredentialModel, AddressModel, ShippingLabelModel, ShippingLabelModel_Pydantic
from core.log import logger
from ..common.builders import build_gls_delivery_from_address, build_gls_single_parcel
from utils.stringutils import jsonpath


class DhlEuProvider(ILogisticsProvider):
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

    @staticmethod
    def is_ship_to_station(address_content: str):

        if not address_content or not isinstance(address_content, str):
            return False

        text = address_content.lower()

        # DHL 关键词模式（
        kw_patterns = [
            r"\bdhl(?:[\s-]\w+)?",  # 匹配 "DHL" 或 "DHL-Packstation" / "DHL Postfiliale"
            r"\bpack[\s-]?station\b",  # "Packstation" / "Pack Station" / "Pack-Station"
            r"\bpostfiliale\b"  # "Postfiliale"
        ]
        # 检查是否含有 DHL 相关关键词
        if not any(re.search(p, text, re.IGNORECASE) for p in kw_patterns):
            return False

        # 1. 检查是否包含九位数字
        if not re.search(r"\d{9}", address_content):
            return False

        # 两项都满足则返回 True
        return True

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

        address_content = [
            shipping_address.name, shipping_address.company,
            shipping_address.address1, shipping_address.address2,
            order.customer_note
        ]
        text = ";".join(filter(None, address_content))
        if not self._check_address_validity(text):
            raise ShipmentRouteError("This address is not valid for GLS shipment. Please check the order again.")

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
        if isinstance(parcel_numbers, str):
            parcel_numbers = [parcel_numbers]
        track_ids = jsonpath(data, '$.parcels[*].trackId')
        if isinstance(track_ids, str):
            track_ids = [track_ids]
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

    def _check_address_validity(self, address_content: str) -> bool:
        valid = not DhlEuProvider.is_ship_to_station(address_content)
        return valid

    def _add_order_item_to_label(self):
        # TODO: 增加订单项信息到 label 中
        pass