from enum import Enum


class OrderStatus(str, Enum):
    NEW = "new"      # Just pulled from platform
    WAITING_LABEL = "waiting_label"  # Waiting to generate shipping label
    LABEL_CREATED = "label_created"  # Shipping label successfully created
    LABEL_FAILED = "label_failed"  # Failed to create label
    SYNCED = "synced"   # Tracking info synced to platform
    SYNC_FAILED = "sync_failed"  # Failed to sync to platform
    UPLOADED = "uploaded"  # Uploaded to printshop
    UPLOAD_FAILED = "upload_failed"  # Failed to upload to printshop
    COMPLETED = "completed"  # Fully processed
    EXCEPTION = "exception"   # Manual intervention required
    CANCELLED = "cancelled"     # Cancelled order


class OrderBatchStatus(str, Enum):
    PENDING = "pending"  # Batch created but not yet uploaded
    UPLOADED = "uploaded"  # Successfully uploaded to printshop
    UPLOAD_FAILED = "upload_failed"  # Upload to printshop failed
    COMPLETED = "completed"  # Fully processed and marked done


class AddressType(str, Enum):
    SHIPPING = "shipping"
    BILLING = "billing"


class CarrierCode(str, Enum):
    DHL = "DHL"
    GLS_EU = "GLS-EU"
    DPD = "DPD"
    UPS = "UPS"


class ChannelCode(str, Enum):
    WOOCOMMERCE = "woocommerce"
    TIKTOK = "tiktok"
    AMAZON = "amazon"
    KAUFLAND = "kaufland"
    CUSTOM_ERP = "custom_erp"


class OperationType(str, Enum):
    LABEL_GEN = "label_gen"
    SYNC = "sync"
    UPLOAD = "upload"
    PRINT = "print"


class IntegrationType(str, Enum):
    ORDER_CHANNEL = "order_channel"  # Shopify, JD 等
    LOGISTICS = "logistics"  # DHL, UPS 等
    OTHER = "other"  # 预留扩展（短信、支付等）
