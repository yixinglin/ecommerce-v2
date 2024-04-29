import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.db import init_db_sqlite
from core.log import logger
from fastapi.responses import JSONResponse
from schemas.basic import CodeEnum
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
    err_detail = traceback.format_exc()
    logger.error(f"An exception occurred: {err_detail}")
    return JSONResponse(status_code=int(CodeEnum.InternalServerError.value),
                        content={"message": f"Internal server error. \n{err_detail}"})

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """
    Runtime exception handler
    """
    logger.error(f"A runtime error occurred: {exc}")
    return JSONResponse(status_code=int(CodeEnum.Fail.value),
                        content={"message": str(exc)})

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
    # response.headers["Cache-Control"] = "max-age=3600, public"
    # headers = {"Cache-Control": "max-age=3600, public"},
    return response
