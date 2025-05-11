import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config2 import settings
from core.db import init_db_mysql_for_app
from core.log import logger
from fastapi.responses import JSONResponse
from schemas.basic import CodeEnum
from .v1 import v1
import os

app = FastAPI(title=settings.app.project_name,
              version=settings.app.version,
              openapi_url=f"{settings.app.prefix}/openapi.json",
              summary="Microservice API simplifying e-commerce processes",
              contact={
                  "name": "YX. Lin",
                  "email": "184059914@qq.com",
                  "url": "https://github.com/yixinglin"
              },
              docs_url=f"{settings.app.prefix}/docs",
              )


app.include_router(v1, prefix=settings.app.prefix)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],   # Allows all headers
)

# http://127.0.0.1:8000/static/images/logo.png
os.makedirs(settings.static.static_dir, exist_ok=True)
os.makedirs(settings.static.upload_dir, exist_ok=True)
os.makedirs(settings.static.image_dir, exist_ok=True)
app.mount("/static2",
          StaticFiles(directory=settings.static.static_dir),
          name="static2")

ASSETS = "./assets"
os.makedirs(f"{ASSETS}/media", exist_ok=True)
app.mount("/media", StaticFiles(directory=f"{ASSETS}/media"), name="media")
os.makedirs(f"{ASSETS}/static", exist_ok=True)
app.mount("/static", StaticFiles(directory=f"{ASSETS}/static"), name="static")
os.makedirs(f"{ASSETS}/pic", exist_ok=True)
app.mount("/pic", StaticFiles(directory=f"{ASSETS}/pic"), name="pic")




# init_db_sqlite(app)
init_db_mysql_for_app(app)

from schedule import hourly_scheduler, daily_scheduler, async_hourly_scheduler


@app.on_event("startup")
async def startup_event():
    logger.info("Starting scheduler")
    logger.info(settings)
    hourly_scheduler.start()
    daily_scheduler.start()
    async_hourly_scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping scheduler")
    hourly_scheduler.shutdown()
    daily_scheduler.shutdown()
    async_hourly_scheduler.shutdown()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    err_detail = traceback.format_exc()
    logger.error(f"An exception occurred: {err_detail}")
    return JSONResponse(status_code=int(CodeEnum.InternalServerError.value),
                        content={"message": f"Internal server error. \n{exc}"})

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
    logger.info(f"Request: [{request.method}] {request.url}, Client IP: {client_ip}")
    # Continue processing the request
    response = await call_next(request)
    # Return response information
    logger.info(f"Response: {response.status_code}")
    # response.headers["Cache-Control"] = "max-age=3600, public"
    # headers = {"Cache-Control": "max-age=3600, public"},
    return response

@app.get("/")
async def root():
    return {"message": "Welcome to the Ecommerce Service"}
