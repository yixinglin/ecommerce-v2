import asyncio
from decimal import Decimal
from typing import List
from tortoise.transactions import in_transaction
from core.log import logger
from ..common.enums import ChannelCode, OrderStatus, CarrierCode, AddressType, IntegrationType
from ..interfaces import IOrderChannel, Order
from ..models import IntegrationCredentialModel, OrderModel, AddressModel, OrderModel_Pydantic, OrderItemModel, \
    OrderStatusLogModel, OrderErrorLogModel, ShippingLabelModel
from external.woocommerce.wpapi import ApiKey as WC_API_Key
from external.woocommerce.extent import OrderClient as WooOrderClient, TrackInfoUpdate



class OrderRepository:
    @staticmethod
    async def exists(order_number: str, account_id: str, channel: str) -> bool:
        return await OrderModel.filter(order_number=order_number, account_id=account_id, channel=channel).exists()

    @staticmethod
    async def save_order(
            order_data: dict, shipping_data: dict, billing_data:
            dict, order_items: List[dict]
    ) -> OrderModel_Pydantic:

        # Sort by quantity
        order_items = list(sorted(order_items, key=lambda x: x['quantity'], reverse=True))

        # Build sort key for orders
        item = order_items[0]
        sort_key = f"{item['sku']}x{item['quantity']}"
        order_data['sort_key'] = sort_key

        async with in_transaction():
            shipping_addr = await AddressModel.create(**shipping_data)
            billing_addr = await AddressModel.create(**billing_data)
            order_data["shipping_address_id"] = shipping_addr.id
            order_data["billing_address_id"] = billing_addr.id
            new_order = await OrderModel.create(**order_data)
            for item in order_items:
                await OrderItemModel.create(
                    order_id=new_order.id,
                    **item
                )
            return await OrderModel_Pydantic.from_tortoise_orm(new_order)

    @staticmethod
    async def delete_order(order_id: int):
        async with in_transaction():
            order = await OrderModel.get(id=order_id)
            if not order:
                logger.error(f"Order {order_id} not found")
                raise Exception(f"Order {order_id} not found")
            await AddressModel.filter(id=order.shipping_address_id).delete()
            await AddressModel.filter(id=order.billing_address_id).delete()
            await OrderItemModel.filter(order_id=order_id).delete()
            await OrderStatusLogModel.filter(order_id=order_id).delete()
            await OrderErrorLogModel.filter(order_id=order_id).delete()
            await ShippingLabelModel.filter(order_id=order_id).delete()
            await order.delete()
            return {"message": "Order deleted successfully"}

class WooCommerceChannel(IOrderChannel):
    def __init__(self):
        self.credential: IntegrationCredentialModel = None

    def set_credential(self, cred: IntegrationCredentialModel):
        self.credential = cred
        self.api_key = WC_API_Key(
            name=self.credential.name,
            username=self.credential.api_key,
            password=self.credential.api_secret,
            url=self.credential.meta.get("base_url"),
            version=self.credential.meta.get("version")  # "wc/v3"
        )

    def get_channel_code(self) -> str:
        return ChannelCode.WOOCOMMERCE

    async def get_pending_orders(self) -> List[OrderModel_Pydantic]:
        """
        Pull orders from WooCommerce with 'processing' [or 'on-hold'] status
        获取代发货状态的订单. 因平台而异, 可能是 'processing' 或 'confirmed' 状态.
        获取订单之后储存到数据库内。
        """
        external_orders = await asyncio.to_thread(
            self._fetch_orders_from_channel,
            status=['processing'],
            per_page=99
        )
        orders: List[Order] = []
        saved_count = 0
        for ext in external_orders:
            try:
                parsed_data = self._parse_order_data(ext)
                order_data = parsed_data['order']
                if await OrderRepository.exists(
                    order_data['order_number'],
                    self.credential.external_id,
                    self.get_channel_code()
                ):
                    logger.debug(f"Order {order_data['order_number']} exists")
                    continue

                new_order = await OrderRepository.save_order(
                    order_data,
                    parsed_data['shipping'],
                    parsed_data['billing'],
                    parsed_data['order_items']
                )
                logger.info(
                    f"Saved order [id={order_data['order_number']}] from {self.get_channel_code()} | {self.credential.external_id}"
                )
                orders.append(new_order)
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to pull order {e}")
        logger.info(f"Saved {saved_count} new orders")
        return orders

    async def sync_tracking_info(self, order: Order) -> bool:
        """
        Update order on WooCommerce with tracking number
        Requires plugin like 'Shipment Tracking' to work properly
        """
        if not self.credential:
            raise Exception("WooCommerce credential not set")

        if not self.api_key:
            raise Exception("API key not set")

        tracking_number = order.tracking_number
        carrier_code = order.carrier_code
        if not tracking_number or not carrier_code:
            raise Exception("Tracking number or carrier code not set")

        client = WooOrderClient(self.api_key)

        # Update tracking info to WooCommerce
        track_info = TrackInfoUpdate(
            order_id=order.order_number,
            tracking_number=order.tracking_number,
            tracking_url=order.tracking_url,
            carrier=order.carrier_code
        )
        try:
            await asyncio.to_thread(
                client.update_track_info,
                track_info
            )
            logger.info(f"Updated tracking info for order {order.order_number}")
            return True
        except Exception as e:
            logger.info(f"Failed to update tracking info for order {order.order_number} | {e}")
        return False

    def _fetch_orders_from_channel(self, status: List[str], per_page: int = 99):
        if not self.credential:
            raise Exception("WooCommerce credential not set")

        if not self.api_key:
            raise Exception("API key not set")

        params = {
            "status": ",".join(status),  # processing or on-hold
            "per_page": per_page
        }
        client = WooOrderClient(self.api_key)
        processing_orders = client.fetch_orders(params)
        orders = processing_orders.get("data", [])
        total_pages = processing_orders.get("total_pages", 0)
        total = processing_orders.get("total", 0)
        logger.info(f"Fetched orders from {self.get_channel_code()} | {self.credential.external_id}. Pagesize: {per_page}, Status: {status}")
        logger.info(f"Fetched total orders: {total}, Total pages: {total_pages}")
        return orders

    def _parse_order_data(self, data: dict) -> dict:
        bill_data = data.get("billing", {})
        billing_address = {}
        default_carrier = CarrierCode.GLS_EU

        if bill_data:
            billing_address = {
                "name": f"{bill_data.get("first_name", "")} {bill_data.get("last_name", "")}",
                "company": bill_data.get("company", ""),
                "address1": bill_data.get("address_1", ""),
                "address2": bill_data.get("address_2", ""),
                "city": bill_data.get("city", ""),
                "state_or_province": bill_data.get('state', ""),
                "postal_code": bill_data.get('postcode', ""),
                "country": bill_data.get("country", ""),
                "country_code": bill_data.get("country", ""),
                "address_type": AddressType.BILLING,
                "phone": bill_data.get("phone", ""),
                "mobile": "",
                "email": bill_data.get("email", ""),
            }

        ship_data = data.get("shipping", {})
        shipping_address = {}
        if ship_data:
            shipping_address = {
                "name": f"{ship_data.get("first_name", "")} {ship_data.get("last_name", "")}",
                "company": ship_data.get("company", ""),
                "address1": ship_data.get("address_1", ""),
                "address2": ship_data.get("address_2", ""),
                "city": ship_data['city'],
                "state_or_province": ship_data.get('state', ""),
                "postal_code": ship_data.get('postcode', ""),
                "country": ship_data.get("country", ""),
                "country_code": ship_data.get("country", ""),
                "address_type": AddressType.SHIPPING,
                "phone": ship_data.get("phone", ""),
                "mobile": "",
                "email": billing_address.get("email", ""),
            }

        buyer_address = f"{shipping_address.get("address1", "")}, {shipping_address.get("postal_code", "")} {shipping_address.get("city", "")}"

        order_items = []
        try:
            for item in data.get("line_items", []):
                convert_str_to_decimal = lambda k: Decimal(str(item.get(k, "0.0")))
                order_items.append({
                    "item_number": str(item.get("id", "")),
                    "name": item.get("name", ""),
                    "sku": item.get("sku", ""),
                    "quantity": item.get("quantity", 1),
                    "unit_price_excl_tax": convert_str_to_decimal("price"),
                    "subtotal_excl_tax": convert_str_to_decimal("subtotal"),
                    "total_incl_tax": convert_str_to_decimal("total") + convert_str_to_decimal("tax_total"),
                    "tax_rate_percent": convert_str_to_decimal("tax_percent"),
                    "image_url": item.get("image", {}).get("src", ""),
                    "raw_data": item
                })
        except Exception as e:
            logger.error(f"Failed to parse order data {e}")

        thumbnail_urls = [item.get("image_url", "") for item in order_items if item.get("image_url", "")]

        order = {
            "order_number": str(data['id']),
            "channel": self.get_channel_code(),
            "account_id": self.credential.external_id,
            "status": OrderStatus.NEW,
            "buyer_name": billing_address.get("name", "") or billing_address.get("company", ""),
            "buyer_address": buyer_address,
            "country_code": billing_address.get("country_code", ""),
            "carrier_code": default_carrier,
            "customer_note": data.get("customer_note", ""),
            "thumbnails": ",".join(thumbnail_urls),
            "raw_data": data
        }

        return dict(
            order=order,
            shipping=shipping_address,
            billing=billing_address,
            order_items=order_items
        )


