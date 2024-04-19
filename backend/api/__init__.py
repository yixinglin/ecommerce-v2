
from fastapi import FastAPI
from core.config import settings
from .v1 import v1
import os

app = FastAPI(title=settings.PROJECT_NAME,
              version=settings.API_VERSION,
              openapi_url=f"{settings.API_PREFIX}/openapi.json",
              docs_url=f"{settings.API_PREFIX}/docs",
              )


app.include_router(v1, prefix=os.environ['API_PREFIX'])