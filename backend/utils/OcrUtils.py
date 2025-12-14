"""
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-chi-sim  # 简体中文


"""

import base64
from io import BytesIO
from PIL import Image
from pydantic import BaseModel
from pytesseract import pytesseract

class ImageParams(BaseModel):
    image: str  # base64 格式
    language: str  # 语言, chi_sim, eng, jpn, kor, deu, fra, ita, pol, nld, spa, deu+eng


def ocr_image(params: ImageParams) -> dict:
    base64_str = params.image
    if not base64_str:
        return {"text": "", "error": "No image provided"}

    try:
        # 去掉前缀：data:image/png;base64,
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]

        # 解码 Base64
        img_bytes = base64.b64decode(base64_str)
        image = Image.open(BytesIO(img_bytes))

        # OCR 识别
        config = r"--oem 3 --psm 6 -c preserve_interword_spaces=1"
        lang = params.language or "deu+eng"
        text = pytesseract.image_to_string(image, lang=lang, config=config)

        # 清洗换行和空白
        text = text.strip()

        return {"text": text}

    except Exception as e:
        return {"text": "", "error": str(e)}