import os
import time
from typing import List
import datetime
from fastapi import APIRouter, UploadFile, HTTPException
import hashlib

common_router = APIRouter()

valid_extensions = [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".txt", ".csv", ".jpg", ".jpeg", ".png", ".gif"]

@common_router.post("/file-upload", response_model=dict)
async def file_upload(file: UploadFile):
    upload_dir = os.path.join("static2", "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    original_filename = file.filename
    # 获取文件扩展名（包含点，如 .pdf）
    extension = os.path.splitext(original_filename)[1]
    filename = original_filename.replace(extension, "")
    if ";" in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain semicolon (;).")
    if extension.lower() not in valid_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension.")
    now_ = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M')
    new_filename = f"{filename}_{now_}{extension}"
    file_location = os.path.join(upload_dir, new_filename)
    # 保存文件
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": new_filename}


@common_router.post("/file-upload-without-name", response_model=dict)
async def file_upload_without_name(file: UploadFile):
    # TODO: 测试这个函数file_upload_without_name
    upload_dir = os.path.join("static2", "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    original_filename = file.filename
    # 获取文件扩展名（包含点，如 .pdf）
    extension = os.path.splitext(original_filename)[1]
    if extension.lower() not in valid_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension.")

    filename_hash = original_filename + str(time.time())
    filename_hash = hashlib.md5(filename_hash.encode()).hexdigest()
    new_filename = f"{filename_hash}{extension}"
    file_location = os.path.join(upload_dir, new_filename)
    # 保存文件
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": new_filename}
