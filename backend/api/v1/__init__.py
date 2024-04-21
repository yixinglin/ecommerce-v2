from fastapi import APIRouter
from .routes.user import user
from .routes.amazon import amz_order

amz = APIRouter(prefix="/amazon")
amz.include_router(amz_order)

v1 = APIRouter(prefix='/v1')
v1.include_router(user)
v1.include_router(amz)
