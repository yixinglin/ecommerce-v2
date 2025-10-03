from abc import ABC, abstractmethod
from typing import List, Optional
from .models import OrderModel as Order, IntegrationCredentialModel as IntegrationCredential, OrderModel_Pydantic, \
    ShippingLabelModel_Pydantic


class IOrderChannel(ABC):

    @abstractmethod
    def set_credential(self, credential: IntegrationCredential):
        """Set integration credentials"""
        pass

    @abstractmethod
    def get_channel_code(self) -> str:
        """Return unique channel identifier (e.g., 'shopify')"""
        pass

    @abstractmethod
    async def get_pending_orders(self) -> List[OrderModel_Pydantic]:
        """Pull new orders with 'pending shipment' status"""
        pass

    @abstractmethod
    async def sync_tracking_info(self, order: Order) -> bool:
        """Upload tracking number to the platform"""
        pass

class ILogisticsProvider(ABC):

    @abstractmethod
    def set_credential(self, credential: IntegrationCredential):
        """Set integration credentials"""
        pass

    @abstractmethod
    async def create_shipping_label(self, order: Order) -> ShippingLabelModel_Pydantic:
        """Create shipping label and return tracking info"""
        pass

    @abstractmethod
    def get_carrier_code(self) -> str:
        """Return logistics provider code (e.g., 'SF', 'UPS')"""
        pass

