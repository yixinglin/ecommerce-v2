import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "logs"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建一个Streamhandler，将INFO级别或更高级别的日志输出到控制台
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建一个文件处理程序，将INFO级别的日志写入文件
info_file_handler = TimedRotatingFileHandler(os.path.join(LOG_DIR, "info.log"), when="W0", backupCount=12) # 按周日切割日志
info_file_handler.setLevel(logging.INFO)

# 创建一个文件处理程序，将ERROR级别的日志写入文件
error_file_handler = TimedRotatingFileHandler(os.path.join(LOG_DIR, "error.log"), when="W0", backupCount=12)
error_file_handler.setLevel(logging.ERROR)

# 创建格式化器并将其附加到文件处理程序
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
info_file_handler.setFormatter(formatter)
error_file_handler.setFormatter(formatter)


# 将文件处理程序添加到日志记录器
logger.addHandler(console_handler)
logger.addHandler(info_file_handler)
logger.addHandler(error_file_handler)