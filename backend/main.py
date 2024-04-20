import os
from api import app
from uvicorn import run
from core.config import settings

# export $(grep -v '^#' conf/dev.env | xargs) && printenv  && uvicorn main:app --reload
#

if __name__ == '__main__':
    run("main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL)