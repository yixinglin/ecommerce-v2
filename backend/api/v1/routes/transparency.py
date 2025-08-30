from io import BytesIO
from typing import Dict, List, Tuple, Optional
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, Form
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from models.amazon_print import TransparencyCode_Pydantic, TransparencyCodeStatus, TransparencyCodePrintLog_Pydantic
from services.printshop.transparency_code import TransparencyCodeService, BatchInformation

transparency_router = APIRouter()

class BatchInformationResponse(BaseModel):
    data: List[BatchInformation]
    total: int

class TransparencyCodeResponse(BaseModel):
    data: List[TransparencyCode_Pydantic]
    total: int

class TransparencyCodeStatusUpdateResponse(BaseModel):
    total: int
    status: int
    status_name: str
    data: List[TransparencyCode_Pydantic]

class SaveTransparencyBatchResponse(BaseModel):
    batch_id: str
    listing_id: str
    filename: str
    total: int

class PrintLogResponse(BaseModel):
    data: List[TransparencyCodePrintLog_Pydantic]
    total: int

@transparency_router.post("/transparency/upload")
async def upload_transparency(
        filename: str = Form(...),
        listing_id: str = Form(...),
        created_by: str = Form(...),
):
    """
    Upload a transparency code batch file.
    """
    async with TransparencyCodeService() as service:
        results = await service.save_transparency_batch(filename, listing_id, created_by)
    return results

@transparency_router.post("/transparency/upload/smart")
async def smart_upload_transparency(filenames: List[str] = Form(...),
                                    created_by: str = Form(...)):
    """
    Upload multiple transparency code batch files.
    The filenames should be in the format of "TCodes_PID4890922130103254976_FBA-HANS-751416D-5_04260715494075.pdf".
    """
    async with TransparencyCodeService() as service:
        results = await service.smart_save_transparency_batch(filenames, created_by)
    return results

@transparency_router.get("/transparency/batch/info/listing/{listing_id}",
                         response_model=BatchInformationResponse)
async def get_batch_information_by_lid(listing_id: str):
    """
    Get batch information by listing id.
    """
    async with TransparencyCodeService() as service:
        results = await service.get_batch_information_by_lid(listing_id)
    return results

@transparency_router.get("/transparency/batch/info/all",
                         response_model=BatchInformationResponse)
async def get_batch_information():
    """
    Get batch information for all batches.
    :return:
    """
    async with TransparencyCodeService() as service:
        results = await service.get_batch_information()
    return results

@transparency_router.get("/transparency/batch/{batch_id}/all",
                         response_model=TransparencyCodeResponse)
async def get_transparency_code_batch(batch_id: str) -> Dict:
    """
    Get all transparency codes by batch id.
    """
    async with TransparencyCodeService() as service:
        results = await service.get_transparency_codes_by_bid(batch_id)
    return results

@transparency_router.get("/transparency/batch/{batch_id}/unused/{quantity}",
                         response_model=TransparencyCodeResponse)
async def get_unused_transparency_codes_by_bid(batch_id: str, quantity: int):
    """
    Get unused transparency codes by batch id.
    """
    async with TransparencyCodeService() as service:
        results = await service.get_unused_transparency_codes_by_bid(batch_id, quantity)
    return results

@transparency_router.get("/transparency/listing/{listing_id}/unused/{quantity}",
                         response_model=TransparencyCodeResponse)
async def get_unused_transparency_codes_by_lid(listing_id: str, quantity: int):
    """
    Get unused transparency codes by listing id.
    """
    async with TransparencyCodeService() as service:
        results = await service.get_unused_transparency_codes_by_lid(listing_id, quantity)
    return results

@transparency_router.get("/transparency/batch/old/{days_ago}/used",
                         response_model=Dict)
async def get_old_used_transparency_code_ids(days_ago: int) -> Dict:
    """
    Delete unused transparency codes that are older than the given number of days.

    DELETE FROM transparency_code
        WHERE status != 0
        AND updated_at < NOW() - INTERVAL 10 DAY;
    :param days_ago:
    :return:
    """
    async with TransparencyCodeService() as service:
        results = await service.get_old_used_transparency_code_ids(days_ago)
    return results

@transparency_router.get("/transparency/statistics/all",
                         response_model=Dict)
async def get_overall_transparency_code_statistics():
    """
    Get overall transparency code statistics.
    """
    async with TransparencyCodeService() as service:
        results = await service.get_overall_transparency_code_statistics()
    return results

@transparency_router.get("/transparency/statistics/sku",
                         response_model=Dict)
async def get_sku_statistics():
    """
    Get SKU statistics.
    """
    async with TransparencyCodeService() as service:
        results = await service.get_sku_statistics()
    return results

@transparency_router.get(
    "/transparency/statistics/sku/download",
    response_class=StreamingResponse
)
async def download_sku_statistics():
    async with TransparencyCodeService() as service:
        results = await service.get_sku_statistics()
        df_results = pd.DataFrame([item.dict() for item in results['data']])
        buff = BytesIO()
        df_results.to_excel(buff, index=False)
        buff.seek(0)

    encoded_filename = quote("透明码使用情况汇总")
    return StreamingResponse(
        buff,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={encoded_filename}.xlsx"}
    )


@transparency_router.put("/transparency/mark/used",
                         response_model=TransparencyCodeStatusUpdateResponse)
async def mark_transparency_codes_used(ids: List[int]):
    """
    Mark the given transparency codes as used.
    """
    async with TransparencyCodeService() as service:
        result = await service.update_transparency_codes_status(ids,
                                                                status=TransparencyCodeStatus.USED,
                                                                updated_by="system")
        return result

@transparency_router.put("/transparency/mark/status/{status}",
                         response_model=TransparencyCodeStatusUpdateResponse)
async def mark_transparency_codes(ids: List[int], status: TransparencyCodeStatus):
    """
    Mark the given transparency codes with the given status.
    """
    async with TransparencyCodeService() as service:
        result = await service.update_transparency_codes_status(ids,
                                                                status=status,
                                                                updated_by="system")
        return result

class GenerateTransparencyPdfRequest(BaseModel):
    ids: List[int]
    crop_box: Optional[Tuple[float, float, float, float]] = None
    inline: bool = False

from fastapi.responses import Response

@transparency_router.post("/transparency/generate/pdf",
                          response_class=Response,)
async def generate_transparency_pdf_by_ids(body: GenerateTransparencyPdfRequest):
    """
    Generate a PDF file for the given transparency codes.
    :param ids: list of transparency code ids.
    :param inline: whether to display the pdf inline or download it.
    :return: A pdf file for user to download.
    """
    ids = body.ids
    crop_box = body.crop_box
    inline = body.inline
    async with TransparencyCodeService() as service:
        pdf_bytes = await service.generate_transparency_pdf_by_ids(code_ids=ids, crop_box=crop_box)

    filename = "transparency"
    if inline:
        disposition = f"inline; filename={filename}.pdf"
    else:
        disposition = f"attachment; filename={filename}.pdf"

    headers = {
        "Content-Disposition": disposition,
        "Content-Length": str(len(pdf_bytes))
    }

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers
    )

@transparency_router.delete("/transparency/batch/hash/{hash_}/all")
async def delete_transparency_code_by_hash(hash_: str):
    """
    Delete all transparency codes by hash.
    """
    async with TransparencyCodeService() as service:
        result = await service.delete_transparency_code_by_hash(hash_)
    return result

@transparency_router.get("/transparency/logs/listing/{listing_id}",
                         response_model=PrintLogResponse)
async def get_print_logs(listing_id: str):
    """
    Get print logs for a listing.
    """
    async with TransparencyCodeService() as service:
        result = await service.get_print_logs(listing_id)
    return result

"""

很好，以下是你现有的接口路径与推荐优化命名的对照表（保持功能不变，仅路径命名更符合 REST 规范）：

---

## ✅ 接口重命名建议对照表

| 原路径                                                        | 建议路径                                                                             | 说明                         |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------- |
| `POST /transparency/upload`                                | `POST /transparency/batch/upload`                                                | 明确上传的是“batch”资源            |
| `POST /transparency/upload/smart`                          | `POST /transparency/batch/upload-smart`                                          | 统一风格，动词后缀变为 `upload-smart` |
| `GET /transparency/batch/info/listing/{listing_id}`        | `GET /transparency/batches?listing_id={listing_id}`                              | 使用 query param 更灵活，可扩展     |
| `GET /transparency/batch/info/all`                         | `GET /transparency/batches`                                                      | 获取所有批次                     |
| `GET /transparency/batch/{batch_id}/all`                   | `GET /transparency/batch/{batch_id}/codes`                                       | `/all` 不直观，用资源名更清晰         |
| `GET /transparency/batch/{batch_id}/unused/{quantity}`     | `GET /transparency/batch/{batch_id}/codes?status=unused&limit={quantity}`        | 用 query 表达条件               |
| `GET /transparency/listing/{listing_id}/unused/{quantity}` | `GET /transparency/codes?listing_id={listing_id}&status=unused&limit={quantity}` | 更 RESTful，更灵活              |
| `GET /transparency/batch/old/{days_ago}/used`              | `GET /transparency/codes?status=used&older_than={days_ago}`                      | 路径中避免混入逻辑条件                |
| `PUT /transparency/mark/used`                              | `PUT /transparency/codes/status`                                                 | 用统一接口传入 `status=used`      |
| `PUT /transparency/mark/status/{status}`                   | `PUT /transparency/codes/status`                                                 | `status` 统一放入 body         |
| `POST /transparency/generate/pdf`                          | `POST /transparency/codes/pdf`                                                   | 动词放在资源之后，表示“生成资源的表示形式”     |
| `DELETE /transparency/batch/hash/{hash_}/all`              | `DELETE /transparency/codes?hash={hash_}`                                        | 更灵活且可复用的接口风格               |
| `GET /transparency/logs/listing/{listing_id}`              | `GET /transparency/logs?listing_id={listing_id}`                                 | query param 更清晰            |

---

## ✅ 总体重构建议：

* 路径层级：建议统一资源 → 操作 → 条件（如：`/batch/{id}/codes` 或 `/codes?filter=x`）
* 动作表达：`POST`, `PUT`, `DELETE` 已表示意图，路径中不必再冗余 `mark`, `get`, `delete`
* 查询表达：逻辑条件推荐用 query string，如 `?status=used&older_than=30`
* 返回资源明确性：接口应命名为返回的资源类型，不是行为描述

---

是否需要我进一步帮你出一个 Swagger/OpenAPI 文档模板来配合这些命名？





"""