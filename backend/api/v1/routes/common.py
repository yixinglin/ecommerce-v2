import os
from typing import List
import datetime
from fastapi import APIRouter, UploadFile, HTTPException

common_router = APIRouter()
@common_router.post("/file-upload", response_model=dict)
async def file_upload(file: UploadFile):
    upload_dir = os.path.join("static2", "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    original_filename = file.filename
    # 获取文件扩展名（包含点，如 .pdf）
    extension = os.path.splitext(original_filename)[1]
    filename = original_filename.replace(extension, "")
    if ";" in filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain semicolon (;).")
    if extension.lower() not in [".pdf", ".excel", ".docx", ".txt", ".csv", ".jpg", ".jpeg", ".png", ".gif"]:
        raise HTTPException(status_code=400, detail="Invalid file extension.")
    now_ = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M')
    new_filename = f"{filename}_{now_}{extension}"
    file_location = os.path.join(upload_dir, new_filename)
    # 保存文件
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": new_filename}