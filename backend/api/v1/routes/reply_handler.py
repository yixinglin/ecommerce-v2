from typing import Dict

from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException
from starlette.responses import Response

from app.reply_handler.models import EmailActionModel_Pydantic
from app.reply_handler.schemas import EmailsQueryRequest, EmailBaseResponse, EmailResponse, ProcessEmailRequest, \
    PullEmailsRequest
from app.reply_handler.services import PullEmailsService, ReplyHandlerService
from core.log import logger
from core.response import ListResponse

rh_router = APIRouter()

@rh_router.post("/pull", response_model=Dict)
async def pull_emails(payload: PullEmailsRequest):
    service = PullEmailsService()
    count = await service.pull_emails(payload)
    return {"success_count": count}

@rh_router.get(
    "/emails",
    response_model=ListResponse[EmailBaseResponse],
)
async def list_emails(query: EmailsQueryRequest = Depends()):
    try:
        resp = await ReplyHandlerService.list_emails(query)
    except Exception as e:
        logger.error(f"Error while listing emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return resp.dict()

@rh_router.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(email_id: int):
    resp = await ReplyHandlerService.get_email_by_id(email_id)
    return resp

@rh_router.get(
    "/emails/{email_inbox_id}/actions",
    response_model=ListResponse[EmailActionModel_Pydantic]
)
async def list_actions(email_inbox_id: int):
    resp = await ReplyHandlerService.list_actions(email_inbox_id)
    return resp


@rh_router.post("/emails/{email_id}/process", response_model=EmailResponse)
async def process_email(email_id: int, payload: ProcessEmailRequest):
    resp = await ReplyHandlerService.process_email(email_id, payload)
    return resp

@rh_router.post("/emails/{email_id}/analyze", response_model=EmailResponse)
async def analyze_email(email_id: int) -> EmailResponse:
    try:
        resp = await ReplyHandlerService.analyze_email(email_id)
    except Exception as e:
        logger.error(f"Error while analyzing email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return resp


@rh_router.post("/emails/report", response_class=Response)
async def export_report():
    stream = await ReplyHandlerService.export_report()
    bytes_ = stream.read()
    filename = "report"
    disposition = f"attachment; filename={filename}.xlsx"
    headers = {
        "Content-Disposition": disposition,
        "Content-Length": str(len(bytes_)),
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return Response(
        bytes_,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

