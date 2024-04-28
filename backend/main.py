import os
from api import app
from uvicorn import run
from core.config import settings

# sed -i 's/\r$//' conf/dev.env
# export $(grep -v '^#' conf/dev.env | xargs) && printenv  && uvicorn main:app --reload
# export $(grep -v '^#' conf/dev.env | xargs) && printenv  && python main.py

if __name__ == '__main__':
    run("main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL)
