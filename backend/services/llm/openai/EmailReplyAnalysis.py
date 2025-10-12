from typing import Dict, Any
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from core.log import logger
from services.llm.common import LLMKeys, load_openai_client
from services.llm.openai.parse_engine import generate_structured_output, DEFAULT_GPT_MODEL

class AnalysisResponse(BaseModel):
    full_summary: str
    suggested_category: str

SYSTEM_PROMPT = (
    "你是一个面向企业客服的德语邮件分析助手。"
    "背景：我们向大量企业客户发送了Newsletter，现在收到大量与Newsletter相关的的回信/退信，需要统一进行分析和归类整理。"
    "目标：帮助中文客服快速处理这些回信/退信。\n"
    "请严格遵循：\n"
    "1) 先准确理解德语原文；"
    "2) 仅输出中文；"
    "3) 严格按照给定 JSON Schema 输出；"
    "4) 分类必须是以下内部枚举值之一："
    "   invalid_email / unsubscribe_request / email_change / keep_subscription / other；"
    "5) 在 full_summary 中用简洁中文合并：翻译要点 + 判定理由 + 建议如何处理。"
    "6) 在 full_summary 中可以使用emoji和Markdown语法, 增强可读性，但不要过度使用。"
)

USER_PROMPT_TEMPLATE = (
    "【待分析的邮件正文（可能为德语/多语混杂）】\n"
    "{email_content}\n\n"
    "【请完成】\n"
    "A) 提供中文要点翻译；\n"
    "B) 明确给出分类（使用内部枚举值）；\n"
    "C) 给出一段中文的处理建议（例如是否加入黑名单、是否保留订阅、是否退订、是否是邮箱更变及新旧地址识别提示等）。"
    "D) 如果邮件中明确支持邮箱已经更变，在你的回答中重点强调。"
)

RESPONSE_SCHEMA: Dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["full_summary", "suggested_category"],
        "properties": {
            "full_summary": {
                "type": "string",
                "description": "中文整合说明：翻译要点 + 分类依据 + 处理建议（合并为一段话）"
            },
            "suggested_category": {
                "type": "string",
                "description": "内部分类枚举值",
                "enum": [
                    "invalid_email",
                    "unsubscribe_request",
                    "keep_subscription",
                    "email_change",
                    "other"
                ]
            }
    },
    # "strict": True  # 严格模式，避免多余字段/错误结构
}

def analyze_email(
        client: OpenAI,
        email_content: str,
        model_name: str = DEFAULT_GPT_MODEL,
) -> AnalysisResponse:
    prompt = USER_PROMPT_TEMPLATE.format(email_content=email_content)
    logger.info(f"Using Model: {model_name}. Prompt Size: {len(prompt)}")
    response = generate_structured_output(
        client,
        temperature=0.5,
        verbose=False,
        model_name=model_name,
        user_prompt=prompt,
        schema_name="EmailReplyAnalysis",
        output_schema=RESPONSE_SCHEMA,
        system_prompt=SYSTEM_PROMPT,
    )
    return AnalysisResponse(**response)

class EmailReplyAnalyzer:
    def __init__(self, model_name: str = DEFAULT_GPT_MODEL):
        self.client: OpenAI = load_openai_client()
        self.model_name = model_name

    def run(self, email_content: str) -> AnalysisResponse:
        return analyze_email(
            self.client,
            email_content,
            model_name=self.model_name
        )

if __name__ == '__main__':
    client = OpenAI(api_key="sk-")
    address = """
Mustermann
Fehrfeld 88
6 Stock
28203 Bremen
"""
    result = analyze_email(client, address)
    print(result)