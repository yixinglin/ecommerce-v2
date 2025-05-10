from api import app
from uvicorn import run
from core.config2 import settings

if __name__ == '__main__':
    run("main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=False,
        log_level=settings.app.log_level,)
