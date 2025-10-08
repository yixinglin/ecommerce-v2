import asyncio
import base64
import io
import zipfile
from datetime import datetime
from typing import Optional, List

from starlette.exceptions import HTTPException
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

import utils.SlipBuilder as sb
import utils.utilpdf as pdf_utils
from app import OrderBatchModel
from core.log import logger
from core.response import ListResponse
from .common.enums import OrderStatus, OrderBatchStatus, IntegrationType, OperationType, AddressType
from .common.exceptions import TrackingInfoSyncError
from .models import OrderModel, ShippingLabelModel, AddressModel, OrderItemModel, OrderStatusLogModel, \
    IntegrationCredentialModel, OrderModel_Pydantic, OrderErrorLogModel, OrderBatchModel_Pydantic, \
    IntegrationCredentialModel_Pydantic, OrderErrorLogModel_Pydantic, OrderStatusLogModel_Pydantic, \
    OrderItemModel_Pydantic, ShippingLabelModel_Pydantic, AddressModel_Pydantic
from .registry import Registry
from .schemas import OrderQueryRequest, OrderResponse, OrderUpdateRequest, IntegrationCredentialResponse, \
    IntegrationCredentialUpdateRequest, OrderItemResponse


class LoggingService:
    @staticmethod
    async def log_transition(order: OrderModel, to_status: str, remarks: str = ""):
        await OrderStatusLogModel.create(
            order_id=order.id,
            from_status=order.status,
            to_status=to_status,
            channel=order.channel,
            remarks=remarks
        )

    @staticmethod
    async def log_error(
            order: OrderModel,
            operation: OperationType,
            message: str,
            retry_count: int = 1
    ):
        await OrderErrorLogModel.create(
            order_id=order.id,
            channel=order.channel,
            operation=operation,
            error_message=message,
            retry_count=retry_count
        )


class BatchIdService:
    @staticmethod
    async def generate_batch_id(channel: str = None) -> str:
        """
        Generate a unique batch ID for today.
        Format: BATCH_{channel}_YYYYMMDD_###
        """
        today_str = datetime.utcnow().strftime("%Y%m%d")

        prefix = f"BATCH_{channel.upper()}_{today_str}_" if channel else f"BATCH_{today_str}_"

        # 查已有批次数量，防止重复
        count = await OrderBatchModel.filter(batch_id__startswith=prefix).count()
        sequence = count + 1

        return f"{prefix}{sequence:03}"


class BatchService:
    except_status_list = [
        OrderStatus.CANCELLED, OrderStatus.EXCEPTION,
        OrderStatus.SYNC_FAILED, OrderStatus.UPLOAD_FAILED,
        OrderStatus.LABEL_FAILED
    ]

    @staticmethod
    async def generate_batch_from_synced_orders(
            channel: str,
            account_id: Optional[str] = None,
            operator: str = "system"
    ) -> Optional[str]:
        """
        从已同步订单中（status = synced 且 batch_id 为空）选出订单，生成新的批次并绑定 batch_id。

        :param channel: 平台类型，如 woocommerce
        :param account_id: 可选，指定卖家账户
        :param operator: 操作人，默认为 system
        :return: 批次号（batch_id），如无订单返回 None
        """
        async with in_transaction():
            # 获取待打包订单
            query = OrderModel.filter(
                status=OrderStatus.SYNCED,  # 已经同步物流信息的订单
                batch_id__isnull=True,  # 尚未绑定批次的订单
                channel=channel
            )

            if account_id:
                query = query.filter(account_id=account_id)

            orders = await query.all()

            if not orders:
                return None

            # 生成批次号
            batch_id = await BatchIdService.generate_batch_id(channel)

            # 创建批次记录
            await OrderBatchModel.create(
                batch_id=batch_id,
                order_count=len(orders),
                status=OrderBatchStatus.PENDING,
                operator=operator
            )

            # 更新订单的 batch_id
            order_ids = [o.id for o in orders]
            await OrderModel.filter(id__in=order_ids).update(batch_id=batch_id)
            return batch_id

    @staticmethod
    async def complete_batch(batch_id: str):
        orders = await OrderModel.filter(batch_id=batch_id).exclude(
            status__in=BatchService.except_status_list
        ).all()
        batch = await OrderBatchModel.get(batch_id=batch_id)
        logger.info(f"Completing {len(orders)} dispatched orders; Batch ID: {batch_id}")

        async with in_transaction():
            for order in orders:
                # Log order status transition
                await LoggingService.log_transition(
                    order,
                    OrderStatus.COMPLETED,
                    f"Order completed by batch {batch_id}"
                )
                # Update order status
                order.status = OrderStatus.COMPLETED
                order.completed_at = datetime.now()
                await order.save()
                logger.info(f"Order {order.order_number} completed")

            batch.status = OrderBatchStatus.COMPLETED
            await batch.save()
            logger.info(f"Batch {batch_id} completed")

    @staticmethod
    async def list_batches(page, limit) -> ListResponse[OrderBatchModel_Pydantic]:
        batches = await (OrderBatchModel.all()
                         .order_by("-created_at")
                         .limit(limit)
                         .offset((page - 1) * limit))
        total = await OrderBatchModel.all().count()
        batch_list = [await OrderBatchModel_Pydantic.from_tortoise_orm(batch) for batch in batches]
        return ListResponse(
            total=total,
            offset=(page - 1) * limit,
            limit=limit,
            data=batch_list
        )

    @staticmethod
    async def download_batch_zip(batch_id: str) -> bytes:
        """
        下载一个批次的打包文件。
        """
        batch = await OrderBatchModel.get_or_none(batch_id=batch_id)
        logger.info(f"Downloading batch {batch_id} as ZIP file")
        zip_bytes = await ZipBuilder.build_batch_zip(batch_id)
        return zip_bytes


class PDFGenerator:
    @staticmethod
    async def generate_picking_list(orders: List[OrderModel]) -> io.BytesIO:
        # 👉 拣货单：按 SKU 汇总
        return io.BytesIO()  # 返回空文件

    @staticmethod
    async def generate_shipping_labels(orders: List[OrderModel]) -> io.BytesIO:
        # 快递单：按 tracking_number 收集已有 label PDF
        bytes_list = []
        for order in orders:
            # Get the most recent label for this order
            label = await ShippingLabelModel.filter(
                order_id=order.id, channel=order.channel
            ).order_by("-created_at").first()
            if not label or not label.label_file_base64:
                logger.error(f"Missing label for order {order.order_number}")
                continue  # 记录缺失日志或异常

            try:
                pdf_bytes: bytes = base64.b64decode(label.label_file_base64)
                if pdf_bytes:
                    bytes_list.append(pdf_bytes)
            except Exception as e:
                logger.error(f"Failed to process label for order {order.order_number}: {e}")
                continue

        if not bytes_list:
            logger.error("No valid shipping labels found")
            return io.BytesIO()  # 返回空文件

        merged_bytes = await asyncio.to_thread(pdf_utils.concat_pdfs_fitz, bytes_list)
        output_stream = io.BytesIO(merged_bytes)
        output_stream.seek(0)
        logger.info(f"Generated shipping labels for batch {orders[0].batch_id}")
        return output_stream

    @staticmethod
    async def generate_packing_slips(orders: List[OrderModel]) -> io.BytesIO:
        # 装箱单：每个订单生成后合并为一个 PDF
        bytes_list = []

        slip_shipper = sb.ShipperInfo(
            name="Hansa GmbH",
            street="Musterstrasse 123",
            city="Hamburg",
            zip="22113",
            country='Deutschland',
            website="https://www.hansa.com"
        )

        for order in orders:
            ship_address = await AddressModel.get_or_none(id=order.shipping_address_id)
            slip_addr = sb.BuyerAddress(
                street=f"{ship_address.address1}, {ship_address.address2}",
                city=ship_address.city,
                zip=ship_address.postal_code,
                country=ship_address.country
            )
            items = await OrderItemModel.filter(order_id=order.id).all()
            slip_items = [
                sb.Item(sku=_item.sku, name=_item.name, qty=_item.quantity, price=_item.unit_price_excl_tax)
                for _item in items
            ]
            slip_order = sb.Order(
                order_id=order.order_number,
                buyer_name=order.buyer_name,
                buyer_address=slip_addr,
                items=slip_items,
                shipper_info=slip_shipper,
            )

            slip_pdf = sb.SlipBuilder.generate_packing_slip(slip_order)
            bytes_list.append(slip_pdf)

        if not bytes_list:
            logger.error("No valid packing slips found")
            return io.BytesIO()  # 返回空文件

        merged_bytes = await asyncio.to_thread(pdf_utils.concat_pdfs_fitz, bytes_list)
        output_stream = io.BytesIO(merged_bytes)
        output_stream.seek(0)
        logger.info(f"Generated packing slips for batch {orders[0].batch_id}")
        return output_stream


class ZipBuilder:
    @staticmethod
    async def build_batch_zip(batch_id: str) -> bytes:
        """
        构建一个包含拣货单、快递单、装箱单的 ZIP 文件，并返回字节内容。
        所有文档均为单个文件，且基于排序后的订单。
        """
        # 获取订单，并排序订单
        orders = await OrderModel.filter(
            batch_id=batch_id
        ).exclude(
            status__in=BatchService.except_status_list
        ).order_by("id")

        if not orders:
            raise ValueError(f"No orders found for batch_id: {batch_id}")

        # 生成三个 PDF 文档（全部为 BytesIO）
        picking_list_pdf: io.BytesIO = await PDFGenerator.generate_picking_list(orders)
        labels_pdf: io.BytesIO = await PDFGenerator.generate_shipping_labels(orders)
        packing_slips_pdf: io.BytesIO = await PDFGenerator.generate_packing_slips(orders)

        # 在内存中创建 ZIP 文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # zip_file.writestr(f"Picking List-{batch_id}.pdf", picking_list_pdf.getvalue())
            zip_file.writestr(f"Shipping Labels-{batch_id}.pdf", labels_pdf.getvalue())
            zip_file.writestr(f"Packing Slips-{batch_id}.pdf", packing_slips_pdf.getvalue())

        zip_buffer.seek(0)
        return zip_buffer.read()

class OrderService:

    def __init__(self, channel_code=None, account_id=None):
        self.channel_code = channel_code
        self.account_id = account_id

    async def init_credentials(self):
        # 获取凭证
        cred = await IntegrationCredentialModel.get_or_none(
            provider_code=self.channel_code,
            external_id=self.account_id,
            type=IntegrationType.ORDER_CHANNEL,
            is_active=True
        )
        if not cred:
            raise ValueError("Active credential not found")
        self.channel_cred = cred

    async def pull_orders(self) -> int:
        channel = Registry.get_channel(self.channel_code)
        channel.set_credential(self.channel_cred)
        logger.info(f"Pulling orders from {self.channel_code} for account {self.account_id}")
        orders = await channel.get_pending_orders()
        success_count = len(orders)
        logger.info(f"Pulled {success_count} orders from {self.channel_code} for account {self.account_id}")
        return success_count

    @staticmethod
    async def get_order(order_id) -> OrderModel_Pydantic:
        order = await OrderModel.get(id=order_id)
        return await OrderModel_Pydantic.from_tortoise_orm(order)

    @staticmethod
    async def list_orders(request: OrderQueryRequest) -> ListResponse[OrderResponse]:
        # 获取订单列表
        filters = Q()
        if request.status:
            filters &= Q(status=request.status)
        if request.channel_code:
            filters &= Q(channel=request.channel_code)
        if request.account_id:
            filters &= Q(account_id=request.account_id)
        if request.order_id:
            filters &= Q(order_number=request.order_id)
        if request.batch_id:
            filters &= Q(batch_id=request.batch_id)

        total = await OrderModel.filter(filters).count()
        offset = (request.page - 1) * request.limit
        limit = request.limit
        orders = await (OrderModel.filter(filters)
                        .order_by("-created_at")
                        .offset(offset)
                        .limit(limit))
        results = []
        for order in orders:
            results.append(await OrderModel_Pydantic.from_tortoise_orm(order))

        results = [OrderResponse(**order.dict()) for order in results]
        resp = ListResponse(
            total=total,
            offset=offset,
            limit=limit,
            data=results
        )
        return resp

    @staticmethod
    async def update_order(order_id: int, update_request: OrderUpdateRequest) -> OrderResponse:
        update_data = update_request.dict(exclude_unset=True)
        if not order_id:
            raise ValueError("Order ID not provided")

        order = await OrderModel.get(id=order_id)
        logger.info(f"Updating order {order.order_number}")
        for key, value in update_data.items():
            setattr(order, key, value)
        await order.save()
        result = await OrderModel_Pydantic.from_tortoise_orm(order)
        return OrderResponse(**result.dict())

    @staticmethod
    async def get_order_items(order_id: int) -> ListResponse[OrderItemResponse]:
        items = await OrderItemModel.filter(order_id=order_id).all()
        results = [
            await OrderItemModel_Pydantic.from_tortoise_orm(item)
            for item in items
        ]
        return ListResponse(
            total=len(results),
            data=results,
            limit=len(results),
            offset=0
        )

    @staticmethod
    async def sync_tracking_info(order_id: int) -> bool:
        order = await OrderModel.get(id=order_id)
        channel = Registry.get_channel(order.channel)
        cred = await IntegrationCredentialModel.get(
            provider_code=order.channel,
            external_id=order.account_id,
            type=IntegrationType.ORDER_CHANNEL,
            is_active=True
        )
        channel.set_credential(cred)

        if order.status not in [OrderStatus.LABEL_CREATED]:
            logger.error(f"Cannot sync tracking info for order {order.order_number} in status {order.status}")
            raise TrackingInfoSyncError("Please create label before syncing tracking info")

        logger.info(f"Syncing tracking info for order {order.order_number}")
        success = await channel.sync_tracking_info(order)
        if success:
            logger.info(f"Tracking info synced for order {order.order_number}")
            await LoggingService.log_transition(
                order, OrderStatus.SYNCED,
                f"Tracking info synced for order {order.order_number}"
            )
            order.status = OrderStatus.SYNCED
            order.synced_at = datetime.now()
            await order.save()
        else:
            logger.error(f"Failed to sync tracking info for order {order.order_number}")
            await LoggingService.log_transition(
                order, OrderStatus.SYNC_FAILED,
                f"Failed to sync tracking info for order {order.order_number}"
            )
            order.status = OrderStatus.SYNC_FAILED
            await order.save()
        return success

    @staticmethod
    async def get_order_errors(order_id: int) -> ListResponse[OrderErrorLogModel_Pydantic]:
        logs = await OrderErrorLogModel.filter(order_id=order_id).order_by("-created_at")
        results = [
            await OrderErrorLogModel_Pydantic.from_tortoise_orm(log)
            for log in logs
        ]
        return ListResponse(
            total=len(results),
            data=results,
            limit=len(results),
            offset=0
        )

    @staticmethod
    async def get_order_status_logs(order_id: int) -> ListResponse[OrderStatusLogModel_Pydantic]:
        logs = await OrderStatusLogModel.filter(order_id=order_id).order_by("-created_at")
        results = [
            await OrderStatusLogModel_Pydantic.from_tortoise_orm(log)
            for log in logs
        ]
        return ListResponse(
            total=len(results),
            data=results,
            limit=len(results),
            offset=0
        )

    @staticmethod
    async def get_address(order_id: int, address_type: AddressType) -> AddressModel_Pydantic:
        order = await OrderModel.get(id=order_id)
        if address_type == AddressType.SHIPPING:
            address_id = order.shipping_address_id
        elif address_type == AddressType.BILLING:
            address_id = order.billing_address_id
        else:
            raise ValueError(f"Invalid address type: {address_type}")

        if not address_id:
            raise DoesNotExist(f"Address not found for order {order.order_number}")

        address = await AddressModel.get(id=address_id)
        return await AddressModel_Pydantic.from_tortoise_orm(address)


class LabelService:

    def __init__(self):
        pass

    async def generate_label(self, order_id, external_logistic_id) -> bool:
        order = await OrderModel.get(id=order_id)

        carrier_code = order.carrier_code
        logistic_cred = await IntegrationCredentialModel.get(
            type=IntegrationType.LOGISTICS,
            provider_code=carrier_code,
            external_id=external_logistic_id,
            is_active=True
        )


        logistics = Registry.get_logistics(logistic_cred.provider_code)
        logistics.set_credential(logistic_cred)
        try:
            label = await logistics.create_shipping_label(order)
            await LoggingService.log_transition(
                order,
                OrderStatus.LABEL_CREATED,
                f"Label created for order {order.order_number}"
            )
            order.tracking_number = label.tracking_number
            order.tracking_url = label.tracking_url
            order.status = OrderStatus.LABEL_CREATED
            await order.save()
            logger.info(f"Label created for order {order.order_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to create label for order {order.order_number}: {e}")
            await LoggingService.log_transition(
                order,
                OrderStatus.LABEL_FAILED,
                f"Failed to create label for order {order.order_number}: {e}"
            )
            await LoggingService.log_error(
                order,
                OperationType.LABEL_GEN,
                f"Failed to create label for order {order.order_number}: {e}",
                order.label_retry_count
            )
            order.status = OrderStatus.LABEL_FAILED
            await order.save()
            return False

    @staticmethod
    async def get_labels(order_id) -> ListResponse[ShippingLabelModel_Pydantic]:
        order = await OrderModel.get(id=order_id)
        labels = await ShippingLabelModel.filter(
            order_id=order_id,
            carrier_code=order.carrier_code
        ).order_by("-created_at")
        results = [
            await ShippingLabelModel_Pydantic.from_tortoise_orm(label)
            for label in labels
        ]
        return ListResponse(
            total=len(results),
            data=results,
            limit=len(results),
            offset=0
        )


class CredentialService:

    def __init__(self):
        pass

    @staticmethod
    async def list_credentials(page, limit) -> ListResponse[IntegrationCredentialResponse]:
        credentials = await (IntegrationCredentialModel
                             .all()
                             .limit(limit)
                             .offset((page - 1) * limit))
        count = await IntegrationCredentialModel.all().count()
        results = []
        for cred in credentials:
            c = await IntegrationCredentialModel_Pydantic.from_tortoise_orm(cred)
            results.append(IntegrationCredentialResponse(**c.dict()))
        return ListResponse(
            total=count,
            offset=(page - 1) * limit,
            limit=limit,
            data=results
        )

    @staticmethod
    async def update_credential(credential_id: int, update_request: IntegrationCredentialUpdateRequest) -> IntegrationCredentialResponse:
        update_data = update_request.dict(exclude_unset=True)
        if not credential_id:
            raise ValueError("Credential ID not provided")

        cred = await IntegrationCredentialModel.get(id=credential_id)
        logger.info(f"Updating credential {cred.id}")
        for key, value in update_data.items():
            setattr(cred, key, value)
        await cred.save()
        result = await IntegrationCredentialModel_Pydantic.from_tortoise_orm(cred)
        return IntegrationCredentialResponse(**result.dict())
