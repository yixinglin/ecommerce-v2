from io import BytesIO
from typing import Dict, List, Tuple, Optional

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
    async with TransparencyCodeService() as service:
        results = await service.save_transparency_batch(filename, listing_id, created_by)
    return results

@transparency_router.post("/transparency/upload/smart")
async def smart_upload_transparency(filenames: List[str] = Form(...),
                                    created_by: str = Form(...)):
    async with TransparencyCodeService() as service:
        results = await service.smart_save_transparency_batch(filenames, created_by)
    return results

@transparency_router.get("/transparency/batch/info/listing/{listing_id}",
                         response_model=BatchInformationResponse)
async def get_batch_information_by_lid(listing_id: str):
    async with TransparencyCodeService() as service:
        results = await service.get_batch_information_by_lid(listing_id)
    return results

@transparency_router.get("/transparency/batch/info/all",
                         response_model=BatchInformationResponse)
async def get_batch_information():
    async with TransparencyCodeService() as service:
        results = await service.get_batch_information()
    return results

@transparency_router.get("/transparency/batch/{batch_id}/all",
                         response_model=TransparencyCodeResponse)
async def get_transparency_code_batch(batch_id: str) -> Dict:
    async with TransparencyCodeService() as service:
        results = await service.get_transparency_codes_by_bid(batch_id)
    return results

@transparency_router.get("/transparency/batch/{batch_id}/unused/{quantity}",
                         response_model=TransparencyCodeResponse)
async def get_unused_transparency_codes_by_bid(batch_id: str, quantity: int):
    async with TransparencyCodeService() as service:
        results = await service.get_unused_transparency_codes_by_bid(batch_id, quantity)
    return results

@transparency_router.get("/transparency/listing/{listing_id}/unused/{quantity}",
                         response_model=TransparencyCodeResponse)
async def get_unused_transparency_codes_by_lid(listing_id: str, quantity: int):
    async with TransparencyCodeService() as service:
        results = await service.get_unused_transparency_codes_by_lid(listing_id, quantity)
    return results

@transparency_router.put("/transparency/mark/used",
                         response_model=TransparencyCodeStatusUpdateResponse)
async def mark_transparency_codes_used(ids: List[int]):
    async with TransparencyCodeService() as service:
        result = await service.update_transparency_codes_status(ids,
                                                                status=TransparencyCodeStatus.USED,
                                                                updated_by="system")
        return result

@transparency_router.put("/transparency/mark/status/{status}",
                         response_model=TransparencyCodeStatusUpdateResponse)
async def mark_transparency_codes_unused(ids: List[int], status: TransparencyCodeStatus):
    async with TransparencyCodeService() as service:
        result = await service.update_transparency_codes_status(ids,
                                                                status=status,
                                                                updated_by="system")
        return result

class GenerateTransparencyPdfRequest(BaseModel):
    ids: List[int]
    crop_box: Optional[Tuple[float, float, float, float]] = None
    inline: bool = False

@transparency_router.post("/transparency/generate/pdf",
                          response_class=StreamingResponse,)
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
        headers = {"Content-Disposition": f"inline; filename={filename}.pdf"}
    else:
        headers = {"Content-Disposition": f"attachment; filename={filename}.pdf"}

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers=headers
    )

@transparency_router.delete("/transparency/batch/{batch_id}/all")
async def delete_transparency_code_by_batch_id(batch_id: str):
    async with TransparencyCodeService() as service:
        result = await service.delete_transparency_code_by_batch_id(batch_id)
    return result

@transparency_router.delete("/transparency/batch/hash/{hash_}/all")
async def delete_transparency_code_by_hash(hash_: str):
    async with TransparencyCodeService() as service:
        result = await service.delete_transparency_code_by_hash(hash_)
    return result

@transparency_router.get("/transparency/logs/listing/{listing_id}",
                         response_model=PrintLogResponse)
async def get_print_logs(listing_id: str):
    async with TransparencyCodeService() as service:
        result = await service.get_print_logs(listing_id)
    return result

# @transparency_router.put("/transparency/mark/locked")
# async def mark_transparency_codes_locked(ids: List[int]):
#     async with TransparencyCodeService() as service:
#         result = await service.update_transparency_codes_status(ids,
#                                                                 status=TransparencyCodeStatus.LOCKED,
#                                                                 updated_by="system")
#         return result
#
# @transparency_router.put("/transparency/mark/deleted")
# async def mark_transparency_codes_deleted(ids: List[int]):
#     async with TransparencyCodeService() as service:
#         result = await service.update_transparency_codes_status(ids,
#                                                                 status=TransparencyCodeStatus.DELETED,
#                                                                 updated_by="system")
#         return result
#
