from typing import Dict
import json
from openai import OpenAI

from services.llm.common import load_openai_client, LLMKeys

DEFAULT_GPT_MODEL = "gpt-4o-mini-2024-07-18"

def generate_structured_output(
        client: OpenAI,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        schema_name: str,
        model_name: str,
        temperature: float = 0.7,
        verbose: bool = False
) -> Dict:
    """
    Generates a structured JSON output from natural language input using ChatGPT,
    aligned with a given JSON schema.
    """
    response = client.responses.create(
        model=model_name,
        temperature=temperature,
        input=[
            {
                "role": "system",
                "content": system_prompt.strip(),
            },
            {
                "role": "user",
                "content": user_prompt.strip(),
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": output_schema,
                "strict": True,
            }
        }
    )
    try:
        results = json.loads(response.output_text)
    except json.JSONDecodeError:
        print(f"Failed to parse model response as JSON output: {response.output_text}")
    # 消耗的token
    if verbose:
        print(response.model)
        print(response.usage.to_json())
    return results


def parse_shipment_address(
        client: OpenAI,
        raw_address: str,
        model_name: str = DEFAULT_GPT_MODEL,
) -> Dict:
    system_prompt = """
You are an expert address normalization and parsing engine, specializing in structured extraction of postal address components across all European countries. You are tasked with converting a single raw address in free-text form into a structured JSON object that is suitable for backend processing in a shipping or logistics system.

Your job is to:
- Extract key components from the address text.
- Normalize the format.
- Ensure that all required fields are filled or defaulted according to logic (e.g., using city name as province if province is missing).
- Output a single JSON object in English, following consistent naming and value formatting.

You must extract the following fields:
- name1: Full recipient name (including title if provided)
- name2: Company name (if applicable)
- name3: Additional information such as department, office, or practice (if present)
- street1: Full street address including street name and building number
- zipCode: Postal or ZIP code
- city: Name of the city or locality
- province: Administrative region or province (default to city if not available)
- country: The ISO 3166-1 alpha-2 code for the country (e.g., DE, FR, IT, ES)
- email: If present in the text, extract and include it
- telephone: If present, extract
- mobile: If present, extract

Guidelines:
- If a field is missing in the text, set its value to an empty string "".
- Be strict with postal structure, but flexible with real-world formatting variations (e.g., no commas or nonstandard line breaks).
- Never invent values. Only extract what is logically and explicitly present or reasonably inferred (e.g., using city as province).
- Country names must be converted to their ISO code representation.
- Output must be a valid and flat JSON object with no nested structures and no additional metadata or explanation.

"""
    response = generate_structured_output(
        client,
        temperature=0.5,
        verbose=False,
        model_name=model_name,
        user_prompt=raw_address,
        schema_name="address_schema",
        output_schema={
            "type": "object",
            "properties": {
                "name1": {"type": "string"},
                "name2": {"type": ["string", "null"]},
                "name3": {"type": ["string", "null"]},
                "street1": {"type": "string"},
                "zipCode": {"type": "string"},
                "city": {"type": "string"},
                "province": {"type": "string"},
                "country": {"type": "string"},
                "email": {"type": ["string", "null"]},
                "telephone": {"type": ["string", "null"]},
                "mobile": {"type": ["string", "null"]},
            },
            "required": ["name1", "name2", "name3", "street1",
                         "zipCode", "city", "province", "country",
                         "email", "telephone", "mobile"],
            "additionalProperties": False,
        },
        system_prompt=system_prompt
    )
    return response


class OpenaiAddressParser:

    def __init__(self, model_name: str = DEFAULT_GPT_MODEL):
        self.client: OpenAI = load_openai_client()
        self.model_name = model_name

    def parse(self, raw_address: str) -> Dict:
        return parse_shipment_address(
            self.client,
            raw_address,
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
    result = parse_shipment_address(client, address)
    print(result)