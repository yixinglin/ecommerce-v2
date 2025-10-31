import os, sys
print("Python interpreter:", sys.executable)
print("CWD:", os.getcwd())
print("PYTHONPATH:", sys.path[:5])



import uvicorn
from api import app
from core.config2 import settings
import os


def start():
    """
    启动 FastAPI 应用程序，适用于本地调试。
    """
    uvicorn.run(
        app,  # 直接传 app 实例，避免慢启动
        host=settings.app.host,
        port=settings.app.port,
        log_level=settings.app.log_level,
        reload=False,  # 关闭 reload，提升调试速度
    )


if __name__ == "__main__":
    # 可选：区分 dev 和 prod 环境
    env = os.getenv("ENV", "dev")
    print(f"Running in {env} mode")

    start()
