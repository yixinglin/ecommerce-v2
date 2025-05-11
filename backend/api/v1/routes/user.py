from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from core.security import hash_password, Token, verify_password, create_access_token, \
    get_current_user, generate_code, verification_codes
from models import User
from models.user import UserCreate, UserOut, ResetPasswordRequest, ForgotPasswordRequest, ResetPasswordByCodeRequest
from schemas import ResponseSuccess

from utils.mail import send_email_background, BackgroundTasks

app = APIRouter(tags=['Authentication'])


@app.post("/register", summary="User Registration")
async def register(user: UserCreate):
    if await User.get_or_none(username=user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if await User.get_or_none(email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    user_obj = await User.create(
        username=user.username,
        password=hashed_pw,
        email=user.email,
        gender=user.gender
    )
    return {"message": "Register success", "user_id": user_obj.id}


@app.get("/userinfo", response_model=UserOut, summary="Get user information")
async def userinfo(current_user: User = Depends(get_current_user)):
    return current_user


# 登录接口（OAuth2PasswordRequestForm 会自动处理表单）
@app.post("/login", response_model=Token, summary="User Login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.get_or_none(username=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Username or password incorrect")

    access_token = create_access_token({"sub": user.username})
    return Token(access_token=access_token)

@app.get('/send-email', summary='Send email')
def send_email(background_tasks: BackgroundTasks,):
    send_email_background("yixing.lin525@gmail.com",
                          'Test email',
                          'This is a test email',
                          background_tasks)
    return ResponseSuccess(data='Email sent successfully')

@app.post("/reset-password", summary="Reset password")
async def reset_password(
    request: ResetPasswordRequest,
    current_user: User = Depends(get_current_user)
):
    # 1. 验证旧密码是否正确
    if not verify_password(request.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Old password incorrect")

    # 2. 加密新密码并保存
    current_user.password = hash_password(request.new_password)
    await current_user.save()

    return {"message": "Password reset successful"}

@app.post("/forgot-password", summary="Send verification code to reset password")
async def forgot_password(req: ForgotPasswordRequest):
    user = await User.get_or_none(email=req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found")

    code = generate_code()
    verification_codes[req.email] = code

    # 模拟发送邮件（实际请对接发信服务）
    print(f"[模拟邮件] 验证码已发送到 {req.email}：{code}")

    return {"message": "Verification code sent"}


@app.post("/reset-password-by-code", summary="Reset password by verification code")
async def reset_password_by_code(req: ResetPasswordByCodeRequest):
    # 验证码校验
    expected_code = verification_codes.get(req.email)
    if not expected_code or expected_code != req.code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    user = await User.get_or_none(email=req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(req.new_password)
    await user.save()

    # 一次性验证码清除
    del verification_codes[req.email]

    return {"message": "Password reset successful"}