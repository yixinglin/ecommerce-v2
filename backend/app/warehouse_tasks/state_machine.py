from typing import Dict, List
from tortoise.timezone import now

from app import WarehouseTaskModel
from app.warehouse_tasks.enums import TaskStatus
from app.warehouse_tasks.state_logger import WarehouseTaskActionLogger


class TaskStateMachine:
    """
    仓库任务状态机

    负责：
    - 判断某个任务当前允许哪些操作（actions）
    - 执行状态流转
    - 自动写入业务时间字段

       前端不允许直接改 status
       所有状态变更必须走这个类
    """

    # 状态 -> 允许的操作 （业务合法性）
    _state_actions: Dict[TaskStatus, List[str]] = {
        TaskStatus.PENDING: [
            "confirm",   # 任务确认（领取）
            "exception",  # 任务异常（拒收）
        ],
        TaskStatus.CONFIRMED: [
            "start",   # 开始执行（备货中）
            "ready",     # 直接备齐（允许跳过执行）
            "exception", # 任务异常（拒收）
        ],
        TaskStatus.PROCESSING: [
            "ready",  # 确认备齐
            "exception", # 任务异常（拒收）
        ],
        TaskStatus.READY: [
            "ship",      # 确认发走
            "exception",  # 任务异常（拒收）
        ],
        TaskStatus.SHIPPED: [
            "complete",  # 确认完成
        ],

        TaskStatus.EXCEPTION: [
            "resume",  # 管理员处理后恢复
            "cancel",  # 直接取消
        ],
    }

    # 操作 -> 新状态 (状态流转）
    _action_to_status: Dict[str, TaskStatus] = {
        "confirm": TaskStatus.CONFIRMED,
        "start": TaskStatus.PROCESSING,
        "ready": TaskStatus.READY,
        "ship": TaskStatus.SHIPPED,
        "complete": TaskStatus.COMPLETED,

        # 异常分支
        "exception": TaskStatus.EXCEPTION,
        "resume": TaskStatus.PENDING,
        "cancel": TaskStatus.CANCELED,
    }

    # 3. 操作元信息（给前端）
    _action_meta: Dict[str, dict] = {
        "confirm": {
            "label": "任务确认",
            "type": "primary",
            "danger": False,
            "confirm": None,
        },
        "start": {
            "label": "开始任务",
            "type": "primary",
            "danger": False,
            "confirm": None,
        },
        "ready": {
            "label": "确认备齐",
            "type": "primary",
            "danger": False,
            "confirm": "确认货物已全部备齐？",
        },
        "ship": {
            "label": "确认发走",
            "type": "primary",
            "danger": False,
            "confirm": "确认司机已提货？",
        },
        "complete": {
            "label": "确认完成",
            "type": "primary",
            "danger": False,
            "confirm": None,
        },
        "exception": {
            "label": "异常处理",
            "type": "default",
            "danger": True,
            "confirm": "遇到问题无法继续，确认标记为异常？",
        },
        "resume": {
            "label": "恢复任务",
            "type": "default",
            "danger": False,
            "confirm": "确认异常已处理，恢复任务？",
        },
        "cancel": {
            "label": "取消任务",
            "type": "default",
            "danger": True,
            "confirm": "确认取消该任务？",
        },
    }

    # 4. 状态 -> 前端可显示的按钮（降低打包员认知负担）
    # _state_visible_actions: Dict[TaskStatus, List[str]] = {
    #     TaskStatus.PENDING: [
    #         "confirm"
    #     ],
    #
    #     TaskStatus.CONFIRMED: [
    #         "start",
    #         "exception",
    #     ],
    #
    #     TaskStatus.PROCESSING: [
    #         "ready",
    #         "exception",
    #     ],
    #
    #     TaskStatus.READY: [
    #         "ship",
    #         "exception",
    #     ],
    #
    #     TaskStatus.SHIPPED: [
    #         "complete",
    #     ],
    #
    #     TaskStatus.EXCEPTION: [
    #         # 默认不展示，交由管理员界面
    #     ],
    # }

    # 角色限制
    # _action_roles = {
    #     "ship": ["admin"],
    # }

    # 对外方法
    @classmethod
    def get_available_actions(cls, task: WarehouseTaskModel) -> List[dict]:
        """
        返回前端可渲染的按钮控制信息
        """
        status = TaskStatus(task.status)

        allowed_actions = cls._state_actions.get(status, [])
        # visible_actions = cls._state_visible_actions.get(status, [])
        visible_actions = allowed_actions

        actions = []

        for action in allowed_actions:
            meta = cls._action_meta[action]

            actions.append({
                "key": action,
                "label": meta["label"],
                "type": meta["type"],
                "danger": meta["danger"],
                "confirm": meta["confirm"],
                "visible": action in visible_actions,
                "enabled": True,
            })

        return actions

    @classmethod
    async def perform_action(
        cls,
        task: WarehouseTaskModel,
        action: str,
        operator: str,
        *,
        exception_type: int | None = None,
        comment: str | None = None,
    ) -> None:
        """
        执行一次状态流转

        :param task: 仓库任务
        :param action: 操作 key（confirm / start / ready / ship / complete）
        :param operator: 操作人（执行人）
        """

        current_status = TaskStatus(task.status)
        allowed_actions = cls._state_actions.get(current_status, [])

        # 校验合法性
        if action not in allowed_actions:
            raise ValueError(
                f"Action '{action}' not allowed for status '{current_status.name}'"
            )

        # 状态变更
        current_status = task.status
        new_status = cls._action_to_status[action]

        # 异常校验
        if action == "exception":
            if not exception_type:
                raise ValueError("异常任务必须指定异常原因")
            task.exception_type = exception_type
            task.is_exception = True

        task.status = new_status

        # 自动写业务时间
        if action in ("confirm", "start"):
            task.executor = operator
            task.executing_at = now()

        if action == "ready":
            task.ready_at = now()

        if action in ("ship", "complete"):
            task.completed_at = now()

        if action == "resume":
            task.is_exception = False
            task.exception_type = None

        await task.save()

        # 写操作日志
        await WarehouseTaskActionLogger.log(
            task_id=task.id,
            task_code=task.code,
            action=action,
            from_status=current_status,
            to_status=new_status,
            operator=operator,
            comment=comment or (f"异常类型: {exception_type}" if action == "exception" else None)
        )



