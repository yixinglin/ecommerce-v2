from app.enums.base import BaseEnum



"""
| Enum                        | 中文名     | 说明         |
| --------------------------- | ------- | ---------- |
| `PENDING`                   | **待领**  | 未被仓库工人领取   |
| `PICKING`                   | **备货**  | 拣货 / 打包进行中 |
| `READY`                     | **备齐**  | 货已备好，待后续   |
| `LABEL_CREATED`             | **打单**  | 面单已开，待打印   |
| `MISSING_TRANSPARENCY_CODE` | **缺透码** | 缺亚马逊透明码    |
| `MISSING_FBA_CODE`          | **缺F码** | 缺 FBA 码    |
| `WAITING_PICKUP`            | **待提**  | 等司机提货      |
| `SHIPPED`                   | **已发**  | 已被司机提走     |
| `OUT_OF_STOCK`              | **缺货**  | 无法执行       |
| `PROBLEM`                   | **异常**  | 需要人工处理     |
| `UNCLEAR`                   | **不清**  | 描述不明确      |
| `COMPLETED`                 | **完成**  | 任务结束       |

"""


class TaskStatus(BaseEnum):
    PENDING = 1
    PICKING = 2
    READY = 3
    WAITING_PICKUP = 4
    SHIPPED = 5
    PROBLEM = 6
    OUT_OF_STOCK = 7
    LABEL_CREATED = 8
    MISSING_TRANSPARENCY_CODE = 9
    MISSING_FBA_CODE = 10
    UNCLEAR = 11
    COMPLETED = 12
    CANCELED = 50

    def meta(self):
        return {
            "value": self.value,
            "label": {
                TaskStatus.PENDING: "待领取",
                TaskStatus.PICKING: "备货中",
                TaskStatus.READY: "已备齐",
                TaskStatus.LABEL_CREATED: "打面单",
                TaskStatus.MISSING_TRANSPARENCY_CODE: "缺透码",
                TaskStatus.MISSING_FBA_CODE: "缺FN码",
                TaskStatus.WAITING_PICKUP: "待提货",
                TaskStatus.SHIPPED: "已发货",
                TaskStatus.OUT_OF_STOCK: "缺货",
                TaskStatus.PROBLEM: "异常",
                TaskStatus.UNCLEAR: "不明确",
                TaskStatus.COMPLETED: "完成",
                TaskStatus.CANCELED: "已取消",
            }[self],
            "color": {
                TaskStatus.PENDING: "#909399",   # 灰：未开始
                TaskStatus.PICKING: "#409EFF",   # 蓝：进行中
                TaskStatus.READY: "#67C23A",     # 绿：已准备
                TaskStatus.LABEL_CREATED: "#E6A23C",  # 橙：需要人工
                TaskStatus.MISSING_TRANSPARENCY_CODE: "#F56C6C",  # 红：阻塞
                TaskStatus.MISSING_FBA_CODE: "#F56C6C",
                TaskStatus.WAITING_PICKUP: "#409EFF",
                TaskStatus.SHIPPED: "#303133",   # 深灰：已流转
                TaskStatus.OUT_OF_STOCK: "#F56C6C",
                TaskStatus.PROBLEM: "#FF4D4F",   # 强红：异常
                TaskStatus.UNCLEAR: "#C0C4CC",
                TaskStatus.COMPLETED: "#67C23A",
                TaskStatus.CANCELED: "#F56C6C",  # 红：已取消
            }[self],
        }


class ShopType(BaseEnum):
    HANSA = 1
    NORD = 2
    CTU = 3
    KAUFLAND = 4
    Woocommerce = 5
    TIKTOK = 6
    OTHER = 99

    def meta(self):
        return {
            "value": self.value,
            "label": {
                ShopType.HANSA: "Hansa",
                ShopType.NORD: "Nord",
                ShopType.CTU: "CTU",
                ShopType.KAUFLAND: "Kaufland",
                ShopType.Woocommerce: "Woocommerce",
                ShopType.TIKTOK: "Tiktok",
                ShopType.OTHER: "Other",
            }[self],
            "color": {
                ShopType.HANSA: "#95BF47",  #  绿
                ShopType.NORD: "#0071CE",  # 蓝
                ShopType.CTU: "#FF5733",   #  橙
                ShopType.KAUFLAND: "#FFC300",  # 黄
                ShopType.Woocommerce: "#F56C6C",  # 红
                ShopType.TIKTOK: "#FFC300",  # 黄
                ShopType.OTHER: "#909399",    # 灰
            }[self],
        }


class LabelType(BaseEnum):
    TRANSPARENCY = 1
    FN = 2
    NONE = 9

    def meta(self):
        return {
            "value": self.value,
            "label": {
                LabelType.TRANSPARENCY: "透明码",
                LabelType.FN: "FN码",
                LabelType.NONE: "不贴码",
            }[self],
            "color": {
                LabelType.TRANSPARENCY: "#409EFF",  # 蓝
                LabelType.FN: "#67C23A",           # 绿
                LabelType.NONE: "#F56C6C",          # 红（阻塞）
            }[self],
        }



class TaskType(BaseEnum):
    FBA = 1
    FBM = 2
    B2B = 3
    OTHER = 99

    def meta(self):
        return {
            "value": self.value,
            "label": {
                TaskType.FBA: "FBA",
                TaskType.FBM: "FBM",
                TaskType.B2B: "B2B",
                TaskType.OTHER: "Other",
            }[self],
            "color": {
                TaskType.FBA: "#409EFF",  # 蓝
                TaskType.FBM: "#67C23A",  # 绿
                TaskType.B2B: "#FF5733",  # 橙
                TaskType.OTHER: "#909399",  # 灰
            }[self],
        }


ENUM_REGISTRY = {
    "wtm-task-status": TaskStatus,
    "wtm-shop-type": ShopType,
    "wtm-label-type": LabelType,
    "wtm-task-type": TaskType
}



