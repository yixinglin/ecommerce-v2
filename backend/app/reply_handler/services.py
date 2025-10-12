import datetime
import io
import json
import os
import re
from html import unescape
from typing import List, Optional

import pandas as pd
from bs4 import BeautifulSoup
from starlette.exceptions import HTTPException
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app import EmailInboxModel, EmailActionModel
from app.reply_handler.enums import EmailStatus, ActionType, EmailCategory
from app.reply_handler.models import EmailActionModel_Pydantic, EmailInboxModel_Pydantic, ProcessedAddressModel, \
    ProcessedAddressModel_Pydantic
from app.reply_handler.schemas import ProcessEmailRequest, EmailsQueryRequest, EmailResponse, \
    EmailBaseResponse, PullEmailsRequest
from core.log import logger
from core.response import ListResponse
from services.llm.openai.EmailReplyAnalysis import EmailReplyAnalyzer
from utils.imap_client import ImapClient


class NewsletterImapClient(ImapClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder = "Inbox"

    @classmethod
    def from_json(cls):
        fname = os.path.join('conf', 'emails', 'imap.json')
        with open(fname, "r") as fp:
            config = json.load(fp)
            newsletter_cli = config.get("newsletter")
            if not newsletter_cli:
                raise ValueError("No 'newsletter' section in imap.json")
        return cls(
            server=newsletter_cli.get("server"),
            username=newsletter_cli.get("username"),
            password=newsletter_cli.get("password"),
            port=newsletter_cli.get("port", 993),
            folder=newsletter_cli.get("folder", "Inbox"),
        )


class PullEmailsService:

    def __init__(self):
        self.client = NewsletterImapClient.from_json()

    async def pull_emails(self, payload: PullEmailsRequest) -> int:
        """
        Pulls latest emails to database.
        :param payload:
        :return: Number
        """
        # 拉取邮件
        emails = self.client.fetch_latest_emails(limit=payload.limit)
        inserted_count = 0

        async with in_transaction():
            for mail in emails:
                message_id = mail.get("message_id")
                if not message_id:
                    continue  # 跳过没有 ID 的邮件

                # 判断是否重复
                exists = await EmailInboxModel.filter(message_id=message_id).exists()
                if exists:
                    continue  # 已存在，不再写入

                # 写入数据库
                await EmailInboxModel.create(
                    message_id=message_id,
                    sender=mail["sender_email"],
                    sender_name=mail["sender_name"],
                    recipient=self.client.username,
                    subject=mail["subject"],
                    body=mail["body"],
                    received_at=mail["received_at"] or datetime.datetime.utcnow(),
                    status=EmailStatus.unprocessed,  # 默认未处理
                )
                inserted_count += 1

        return inserted_count


class ReplyHandlerService:

    # @staticmethod
    # async def list_actions_by_email(email_id: int) -> List[EmailActionModel_Pydantic]:
    #     actions = await EmailActionModel.filter(email_id=email_id).order_by("-created_at")
    #     results = [await EmailActionModel_Pydantic.from_tortoise_orm(action) for action in actions]
    #     return results

    @staticmethod
    async def get_email_by_id(email_id: int) -> EmailResponse:
        email = await EmailInboxModel.get_or_none(id=email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        email.body = ReplyHandlerService._preprocess_email_body(email.body)
        result = await EmailInboxModel_Pydantic.from_tortoise_orm(email)
        return result

    @staticmethod
    async def list_emails(query: EmailsQueryRequest) -> ListResponse[EmailBaseResponse]:
        filters = Q()
        if query.category:
            filters &= Q(category=query.category)
        if query.status:
            filters &= Q(status=query.status)
        if query.action_type:
            filters &= Q(action_type=query.action_type)
        if query.keyword:
            filters &= (
                Q(sender__icontains=query.keyword) |
                Q(subject__icontains=query.keyword) |
                Q(body__icontains=query.keyword) |
                Q(recipient__icontains=query.keyword)
            )

        total = await EmailInboxModel.filter(filters).count()
        offset = (query.page - 1) * query.limit
        emails = await (
            EmailInboxModel
            .filter(filters)
            .order_by("-received_at")
            .limit(query.limit)
            .offset(offset)
        )
        results = [await EmailInboxModel_Pydantic.from_tortoise_orm(email) for email in emails]
        results = [EmailBaseResponse(**e.dict()) for e in results]

        resp = ListResponse(
            total=total,
            offset=offset,
            limit=query.limit,
            data=results,
        )
        return resp

    @staticmethod
    async def process_email(email_id: int, payload: ProcessEmailRequest) -> EmailResponse:
        email_obj = await EmailInboxModel.get_or_none(id=email_id)
        if not email_obj:
            raise HTTPException(status_code=404, detail="Email not found")

        # action_type = payload.action_type
        action_map = {
            EmailCategory.invalid_email: ActionType.mark_invalid,
            EmailCategory.email_change: ActionType.email_update,
            EmailCategory.unsubscribe_request: ActionType.unsubscribe,
            EmailCategory.keep_subscription: ActionType.no_action,
            EmailCategory.other: ActionType.no_action,
        }
        action_type = action_map[payload.category]

        # 邮箱发生更变
        if action_type == ActionType.email_update:
            if not payload.old_email or not payload.new_email:
                raise HTTPException(
                    status_code=404,
                    detail="old_email and new_email are required for email_update action"
                )

        async with in_transaction():
            action = await EmailActionModel.create(
                email_inbox_id=email_obj.id,
                action_type=action_type,
                note=payload.note,
                old_email=payload.old_email,
                new_email=payload.new_email,
                user=payload.user
            )

            # 更新主表状态为已处理，并记录处理人/时间
            email_obj.status = EmailStatus.processed
            email_obj.action_type = action_type
            email_obj.category = payload.category
            email_obj.processed_by = payload.user
            email_obj.processed_at = datetime.datetime.utcnow()
            await email_obj.save()

            # 记录邮箱已处理
            processed_address = await ProcessedAddressModel.get_or_none(sender=email_obj.sender)
            if processed_address:
                processed_address.sender_name = email_obj.sender_name
                processed_address.last_new_email = action.new_email
                processed_address.last_action_id = action.id
                processed_address.last_category = payload.category
                processed_address.last_note = action.note
                processed_address.action_count += 1
                await processed_address.save()
            else:
                await ProcessedAddressModel.create(
                    sender=email_obj.sender,
                    sender_name=email_obj.sender_name,
                    last_new_email=action.new_email,
                    last_action_id=action.id,
                    last_category=payload.category,
                    last_note=action.note,
                    action_count=1,
                )

        return await EmailInboxModel_Pydantic.from_tortoise_orm(email_obj)

    @staticmethod
    async def analyze_email(email_id: int) -> EmailResponse:
        email_obj = await EmailInboxModel.get_or_none(id=email_id)
        if not email_obj:
            raise HTTPException(status_code=404, detail="Email not found")

        if email_obj.ai_result_text:
            return await EmailInboxModel_Pydantic.from_tortoise_orm(email_obj)

        email_content = f"""
           Subject: {email_obj.subject}\n\n
           Sender: {email_obj.sender}\n
           Recipient: {email_obj.recipient}\n
           Received at: {email_obj.received_at}\n
           Body:{email_obj.body}        
           """
        # 预处理邮件内容
        email_content = ReplyHandlerService._preprocess_email_body(email_content)
        # 调用 OpenAI 分析
        logger.info(
            f"Analyzing email using OpenAI. Content Length: {len(email_content)}. Content: {email_content[:30]}")
        ai_response = EmailReplyAnalyzer().run(email_content)
        # 保存分析结果
        # email_obj.category = ai_response.suggested_category
        email_obj.ai_result_text = ai_response.full_summary
        await email_obj.save()
        email_response = await EmailInboxModel_Pydantic.from_tortoise_orm(email_obj)
        return email_response

    @staticmethod
    async def export_report() -> io.BytesIO:
        addresses = await ProcessedAddressModel.all().order_by('-updated_at')
        df_results = [await ProcessedAddressModel_Pydantic.from_tortoise_orm(a) for a in addresses]
        df_results = pd.DataFrame([r.dict() for r in df_results])
        for col in df_results.select_dtypes(include=["datetimetz"]).columns:
            df_results[col] = df_results[col].dt.tz_convert(None)
        buff = io.BytesIO()
        df_results.to_excel(buff, index=False)
        buff.seek(0)
        return buff


    @staticmethod
    async def list_actions(email_inbox_id: int) -> ListResponse[EmailActionModel_Pydantic]:
        actions = await EmailActionModel.filter(email_inbox_id=email_inbox_id).order_by("-created_at")
        results = [await EmailActionModel_Pydantic.from_tortoise_orm(action) for action in actions]
        resp = ListResponse(
            total=len(results),
            offset=0,
            limit=len(results),
            data=results,
        )
        return resp

    @staticmethod
    def _preprocess_email_body(raw_body: Optional[str], max_chars: int = 2000) -> str:
        """
          对原始邮件内容进行清洗与压缩，以减少 OpenAI token 消耗。
          返回干净、简短、可供 AI 分析的纯文本。
        """
        if not raw_body:
            return ""

        text = raw_body

        # 解码 HTML 实体，如 &nbsp; &auml; 等
        text = unescape(text)

        # 去除 HTML 标签
        try:
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(separator="\n")
        except Exception:
            # 兜底: 正则硬去标签
            text = re.sub(r"<[^>]+>", "", text)

        # 删除 Base64 块（常见伪附件或图片内嵌）
        text = re.sub(r"[A-Za-z0-9+/=]{100,}", "[附件内容已省略]", text)

        # 删除常见 Data URI（例如 base64 图片）
        text = re.sub(r"data:[^;]+;base64,[A-Za-z0-9+/=]+", "[附件已删除]", text)

        # 统一换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 去除行首尾空格
        lines = [line.strip() for line in text.split("\n")]

        # 删除连续空行（只保留一个）
        cleaned_lines = []
        empty_count = 0
        for line in lines:
            if line == "":
                empty_count += 1
            else:
                empty_count = 0
            if empty_count <= 1:  # 最多保留一个空行
                cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        # 删除段首尾空白空行
        text = text.strip()
        # 再次压缩重复换行（防止多余换行混入）
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 限制长度（避免超出 token 预算）
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...[Content truncated]"

        return text


