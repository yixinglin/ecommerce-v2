from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.db import init_db_sqlite
from core.log import logger
from schemas import ResponseFail
from .v1 import v1
import os

app = FastAPI(title=settings.PROJECT_NAME,
              version=settings.API_VERSION,
              openapi_url=f"{settings.API_PREFIX}/openapi.json",
              docs_url=f"{settings.API_PREFIX}/docs",
              )

app.include_router(v1, prefix=os.environ['API_PREFIX'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],   # Allows all headers
)

init_db_sqlite(app)

from schedule import hourlyScheduler, dailyScheduler


@app.on_event("startup")
async def startup_event():
    logger.info("Starting scheduler")
    logger.info(settings)
    hourlyScheduler.start()
    dailyScheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping scheduler")
    hourlyScheduler.shutdown()
    dailyScheduler.shutdown()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(f"An exception occurred: {exc}")
    return ResponseFail(message="Internal server error", code=500)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log requests
    """
    # Record request information, including client IP address
    client_ip = request.client.host
    logger.info(f"Request: {request.method} {request.url}, Client IP: {client_ip}")
    # Continue processing the request
    response = await call_next(request)
    # Return response information
    logger.info(f"Response: {response.status_code}")
    return response
