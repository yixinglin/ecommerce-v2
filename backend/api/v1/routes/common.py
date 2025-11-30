import os
import time
import datetime
from typing import List

from fastapi import APIRouter, UploadFile, HTTPException
import hashlib

from core.config2 import settings
from utils import OcrUtils
from utils.OcrUtils import ImageParams

common_router = APIRouter()

valid_extensions = [".pdf", ".xls", ".xlsx", ".doc", ".docx",
                    ".txt", ".csv", ".jpg", ".jpeg", ".png", ".gif",
                    ".zip"]
UPLOAD_DIR = settings.static.upload_dir

@common_router.post("/file-upload", response_model=dict)
async def file_upload(file: UploadFile):
    upload_dir = UPLOAD_DIR
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
    month = datetime.datetime.now().strftime('%Y%m')
    upload_dir2 = os.path.join(upload_dir, month)
    os.makedirs(upload_dir2, exist_ok=True)
    file_location = os.path.join(upload_dir2, new_filename)
    # 保存文件
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    file_size = os.path.getsize(file_location)
    new_filename = f"/{month}/{new_filename}"
    return {
        "filename": new_filename,
        "file_size": file_size,
        "original_name": original_filename
    }

@common_router.post("/files-upload", response_model=List[dict])
async def files_upload(files: List[UploadFile]):
    upload_dir = UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    result = []
    for file in files:
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
        month = datetime.datetime.now().strftime('%Y%m')
        upload_dir2 = os.path.join(upload_dir, month)
        os.makedirs(upload_dir2, exist_ok=True)
        file_location = os.path.join(upload_dir2, new_filename)
        # 保存文件
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
        file_size = os.path.getsize(file_location)
        new_filename = f"/{month}/{new_filename}"
        result.append({
            "filename": new_filename,
            "file_size": file_size,
            "original_name": original_filename
        })
    return result


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
    file_size = os.path.getsize(file_location)
    return {"filename": new_filename, "file_size": file_size}

@common_router.post("/ocr", response_model=dict)
async def ocr_image(params: ImageParams):
    result = OcrUtils.ocr_image(params)
    return result