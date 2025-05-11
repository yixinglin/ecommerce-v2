import json
import os.path
from typing import Optional

from core.config2 import settings
from openai import OpenAI
from pydantic import BaseModel, SecretStr


class LLMKeys(BaseModel):
    openai_api_key: Optional[SecretStr] = None
    deepseek_api_key: Optional[SecretStr] = None
    custom_model_key: Optional[SecretStr] = None  # 可扩展项


def load_llm_keys() -> LLMKeys:
    fname = os.path.join("conf", 'apikeys', settings.api_keys.llm_keys)
    with open(fname, "r") as f:
        keys_dict = json.load(f)
    return LLMKeys(**keys_dict)

def load_openai_client() -> OpenAI:
    api_key = load_llm_keys().openai_api_key.get_secret_value()
    if not api_key:
        raise ValueError("OpenAI API key is not set")
    # Validate API key
    if not api_key.startswith("sk-"):
        raise ValueError("Invalid OpenAI API key")
    return OpenAI(api_key=api_key)