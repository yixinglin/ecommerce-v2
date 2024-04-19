import os
from api import app
from uvicorn import run
from core.config import settings

# uvicorn api:app --reload

if __name__ == '__main__':
    run(app, host=settings.API_HOST, port=settings.API_PORT)