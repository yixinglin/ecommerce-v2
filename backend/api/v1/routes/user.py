from fastapi import APIRouter, Depends, Body
from schemas import User_Pydantic, UserIn_Pydantic
from models import User
from schemas import ResponseSuccess, ResponseFail

from utils.mail import send_email_async, send_email_background, BackgroundTasks


user = APIRouter(tags=['user information'])


def get_current_user(token: str) -> User:
    pass

@user.get('/user', summary='Get user information',
          response_model=ResponseSuccess[User_Pydantic])
async def user_info(user: User = Depends(get_current_user)):
    return ResponseSuccess(data=await User_Pydantic.from_tortoise_orm(user))

@user.post('/user', summary='Create user')
async def create_user(user: UserIn_Pydantic):
    return {'message': 'User created successfully'}

@user.get('/send-email', summary='Send email')
def send_email(background_tasks: BackgroundTasks,):
    send_email_background("yixing.lin525@gmail.com",
                          'Test email',
                          'This is a test email',
                          background_tasks)
    return ResponseSuccess(data='Email sent successfully')

# @user.get('/send-email', summary='Send email')
# async def send_email():
#     # await send_email_async("yixing.lin525@gmail.com",
#     #                        'Welcome to our website')
#     # await send_email_async("yixing.lin525@gmail.com", 'Test email', 'This is a test email')
#     await send_email_async("yixing.lin525@gmail.com",
#                           'Test email',
#                           'This is a test email')
#     return ResponseSuccess(data='Email sent successfully')