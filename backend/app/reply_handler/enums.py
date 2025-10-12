from enum import Enum


# ---------- 枚举定义 ----------
class EmailCategory(str, Enum):
    invalid_email = "invalid_email"           # 邮箱失效
    unsubscribe_request = "unsubscribe_request"  # 请求退订
    email_change = "email_change"             # 邮箱更变
    keep_subscription = "keep_subscription"   # 保持订阅
    other = "other"                           # 其他


class EmailStatus(str, Enum):
    unprocessed = "unprocessed"               # 未处理
    processed = "processed"                   # 已处理


class ActionType(str, Enum):
    mark_invalid = "mark_invalid"             # 标记无效邮箱
    unsubscribe = "unsubscribe"               # 退订
    email_update = "email_update"             # 邮箱更变
    no_action = "no_action"                   # 忽略
    other = "other"                           # 其他动作