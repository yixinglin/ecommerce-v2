import datetime

from tortoise.transactions import in_transaction

from core.log import logger
from .common.enums import IntegrationType, CarrierCode
from .common.enums import OrderStatus, OperationType
from .models import IntegrationCredentialModel, OrderStatusLogModel, OrderErrorLogModel, OrderModel
from .interfaces import Order, IOrderChannel, ILogisticsProvider
from .registry import Registry

"""
订单处理编排器
功能：拉取下来的订单进行后续处理
1. 生成快递单
2. 同步跟踪信息
3. 上传到打印店
说明：不包括订单的拉取逻辑。不处理new的订单。
"""
class OrderProcessingFlow:
    def __init__(self, order: Order):
        self.order = order
        self.channel: IOrderChannel = Registry.get_channel(order.channel)
        self.logistics: ILogisticsProvider = Registry.get_logistics(order.carrier_code)

    @classmethod
    async def build_flow(cls, order: Order):
        flow = cls(order)
        await flow.init_credentials()
        return flow

    async def init_credentials(self):
        self.channel_cred = await IntegrationCredentialModel.get(
            type=IntegrationType.ORDER_CHANNEL,
            provider_code=self.order.channel,
            external_id=self.order.account_id,
            is_active=True
        )
        self.channel.set_credential(self.channel_cred)

        self.logistics_cred = await IntegrationCredentialModel.get(
            type=IntegrationType.LOGISTICS,
            provider_code=self.order.carrier_code,
            external_id="2760343751-mock",
            is_active=True
        )
        self.logistics.set_credential(self.logistics_cred)
        pass


    async def run(self):
        logger.info(f"Processing order {self.order.order_number}")
        if self.order.status == OrderStatus.WAITING_LABEL:
            await self._create_label()

        if self.order.status == OrderStatus.LABEL_CREATED:
            await self._sync_tracking()

        # if self.order.status == OrderStatus.SYNCED:
        #     await self._upload_printshop()
        logger.info(f"Order {self.order.order_number} processing completed")

    async def _create_label(self):
        self.order.updated_by = "system"
        if self.order.label_retry_count >= 3:
            logger.error(f"Max retires for label for order {self.order.order_number}")
            async with in_transaction():
                await self._log_transition(OrderStatus.EXCEPTION, "Max retires for label")
                await self._log_error(
                    OperationType.LABEL_GEN,
                    "Max retires for label",
                    self.order.label_retry_count
                )
                self.order.status = OrderStatus.EXCEPTION
                await self.order.save()
            return

        try:
            # raise Exception("Mock Exception")
            label = await self.logistics.create_shipping_label(self.order)
            await self._log_transition(OrderStatus.LABEL_CREATED, "Shipping label created")
            self.order.tracking_number = label.tracking_number
            self.order.tracking_url = label.tracking_url
            self.order.status = OrderStatus.LABEL_CREATED
            await self.order.save()
        except Exception as e:
            logger.error(f"Failed to create label for order {self.order.order_number}: {e}")
            await self._log_transition(OrderStatus.LABEL_FAILED, str(e))
            await self._log_error(OperationType.LABEL_GEN, str(e), self.order.label_retry_count)
            self.order.status = OrderStatus.LABEL_FAILED
            self.order.label_retry_count = (self.order.label_retry_count or 0) + 1
            await self.order.save()


    async def _sync_tracking(self):
        self.order.updated_by = "system"

        if self.order.sync_retry_count >= 3:
            logger.error(f"Max retires for sync for order {self.order.order_number}")
            async with in_transaction():
                await self._log_transition(OrderStatus.EXCEPTION, "Max retires for sync")
                await self._log_error(
                    OperationType.SYNC,
                    "Max retires for sync",
                    self.order.sync_retry_count
                )
                self.order.status = OrderStatus.EXCEPTION
                await self.order.save()
            return


        try:
            # raise Exception("Mock Exception")
            success = await self.channel.sync_tracking_info(self.order)
            if success:
                logger.info(f"Tracking info synced for order {self.order.order_number}")
                await self._log_transition(OrderStatus.SYNCED, "Tracking info synced")
                self.order.status = OrderStatus.SYNCED
                self.order.synced_at = datetime.datetime.now()
            else:
                raise Exception(f"Failed to sync tracking info for order {self.order.order_number}")
        except Exception as e:
            logger.error(f"Failed to sync tracking info for order {self.order.order_number}: {e}")
            await self._log_transition(OrderStatus.SYNC_FAILED, str(e))
            await self._log_error(OperationType.SYNC, str(e), self.order.sync_retry_count)
            self.order.status = OrderStatus.SYNC_FAILED
            self.order.sync_retry_count = (self.order.sync_retry_count or 0) + 1
        finally:
            await self.order.save()


    async def _upload_printshop(self):
        self.order.updated_by = "system"

        if self.order.printshop_retry_count >= 3:
            logger.error(f"Max retires for printshop upload for order {self.order.order_number}")
            async with in_transaction():
                await self._log_transition(OrderStatus.EXCEPTION, "Max retires for printshop upload")
                await self._log_error(
                    OperationType.UPLOAD,
                    "Max retires for printshop upload",
                    self.order.printshop_retry_count
                )
                self.order.status = OrderStatus.EXCEPTION
                await self.order.save()
            return

        try:
            logger.info(f"Uploading order {self.order.order_number} to printshop")
            await self._log_transition(OrderStatus.UPLOADED, "Order uploaded to printshop")
            self.order.status = OrderStatus.UPLOADED
            self.order.uploaded_at = datetime.datetime.now()
        except Exception as e:
            logger.error(f"Failed to upload order {self.order.order_number} to printshop: {e}")
            await self._log_transition(OrderStatus.UPLOAD_FAILED, str(e))
            await self._log_error(OperationType.UPLOAD, str(e), self.order.printshop_retry_count)
            self.order.status = OrderStatus.UPLOAD_FAILED
            self.order.printshop_retry_count = (self.order.printshop_retry_count or 0) + 1
        finally:
            await self.order.save()

    async def _log_transition(self, to_status: str, remarks: str = ""):
        await OrderStatusLogModel.create(
            order_id=self.order.id,
            from_status=self.order.status,
            to_status=to_status,
            channel=self.order.channel,
            remarks=remarks
        )

    async def _log_error(
        self, operation: OperationType,
        message: str,
        retry_count: int = 1
    ):
        await OrderErrorLogModel.create(
            order_id=self.order.id,
            channel=self.order.channel,
            operation=operation,
            error_message=message,
            retry_count=retry_count
        )


async def pull_all_channel_orders():
    creds = await IntegrationCredentialModel.filter(
        type=IntegrationType.ORDER_CHANNEL,
        is_active=True
    )
    logger.info(f"Pulling orders from {len(creds)} channels")
    success_count = 0
    failure_count = 0
    order_count = 0

    for cred in creds:
        channel = cred.provider_code
        channel = Registry.get_channel(channel)
        channel.set_credential(cred)
        try:
            orders = await channel.get_pending_orders()
            success_count += 1
            order_count += len(orders)
        except Exception as e:
            logger.error(f"Error getting orders from {channel}: {e}")
            failure_count += 1
            continue
    logger.info(f"Pull finished. Success: {success_count}, Failure: {failure_count}. Total orders: {order_count}")



