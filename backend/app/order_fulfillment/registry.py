from typing import Dict

from .interfaces import IOrderChannel, ILogisticsProvider
from core.log import logger
from .external.channels import WooCommerceChannel


class Registry:
    order_channels: Dict[str, IOrderChannel] = {}
    logistics_providers: Dict[str, ILogisticsProvider] = {}

    @classmethod
    def register_channel(cls, channel: IOrderChannel):
        cls.order_channels[channel.get_channel_code()] = channel

    @classmethod
    def get_channel(cls, channel_code: str) -> IOrderChannel:
        return cls.order_channels[channel_code]

    @classmethod
    def register_logistics(cls, provider: ILogisticsProvider):
        cls.logistics_providers[provider.get_carrier_code()] = provider

    @classmethod
    def get_logistics(cls, carrier_code: str) -> ILogisticsProvider:
        return cls.logistics_providers[carrier_code]

from .external.logistics import GlsEuProvider

def init_register_channels():
    logger.info("Registering order channels")

    channel_list = [
        WooCommerceChannel(),
    ]

    for channel in channel_list:
        Registry.register_channel(channel)
    logger.info(f"Order channels [{list(Registry.order_channels.keys())}] registered")

def init_register_logistics():
    logger.info("Registering logistics providers")

    provider_list = [
        # DHLProvider(),
        GlsEuProvider()
    ]

    for provider in provider_list:
        Registry.register_logistics(provider)
    logger.info(f"Logistics providers [{list(Registry.logistics_providers.keys())}] registered")