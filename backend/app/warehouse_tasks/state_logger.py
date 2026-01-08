from app.warehouse_tasks.models import WarehouseTaskActionLog
from core.log import logger


class WarehouseTaskActionLogger:
    """
    仓库任务动作日志记录器
    """

    @classmethod
    async def log(
        cls,
        *,
        task_id: int,
        task_code: str,
        action: str,
        from_status: int,
        to_status: int,
        executor: str,
        comment: str | None = None,
    ) -> None:
        """
        写入一条动作日志
        """
        try:
            await WarehouseTaskActionLog.create(
                task_id=task_id,
                task_code=task_code,
                action=action,
                from_status=from_status,
                to_status=to_status,
                executor=executor,
                comment=comment,
            )
        except Exception as e:
            logger.error("Failed to write task action log:", e)


# | 环节        | 起点           | 终点             | 含义      |
# | --------- | ------------ | -------------- | ------- |
# | 待确认 → 已确认 | `created_at` | `confirm` 操作时间 | 任务被领取速度 |
# | 已确认 → 执行中 | `confirm`    | `start`        | 执行响应速度  |
# | 执行中 → 备齐  | `start`      | `ready`        | 备货耗时    |
# | 备齐 → 发走   | `ready`      | `ship`         | 等司机耗时   |
# | 发走 → 完成   | `ship`       | `complete`     | 收尾耗时    |