import logging
import os
from logging.handlers import TimedRotatingFileHandler

from core.config2 import settings

# LOG_DIR = "logs"
LOG_DIR = settings.static.log_dir
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create a file handler for INFO level logs
info_file_handler = TimedRotatingFileHandler(os.path.join(LOG_DIR, "info.log"), encoding="utf-8",
                                             when="W0", backupCount=12) # 按周日切割日志
info_file_handler.setLevel(logging.INFO)

# Create a file handler for ERROR level logs
error_file_handler = TimedRotatingFileHandler(os.path.join(LOG_DIR, "error.log"), encoding="utf-8",
                                              when="W0", backupCount=12)
error_file_handler.setLevel(logging.ERROR)

# Create a formatter for the logs
formatter = logging.Formatter("[%(levelname)s] %(asctime)s | %(message)s", "%Y-%m-%d %H:%M:%S")
info_file_handler.setFormatter(formatter)
error_file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(info_file_handler)
logger.addHandler(error_file_handler)