from fastapi import APIRouter
from .routes.user import user

v1 = APIRouter(prefix='/v1')
v1.include_router(user)