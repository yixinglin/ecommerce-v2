
from fastapi import APIRouter

user = APIRouter(tags=['user information'])

@user.get('/user', summary='Get user information')
async def get_user():
    return {'user': 'John Doe'}