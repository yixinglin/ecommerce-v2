from typing import Dict

from fastapi import APIRouter
from pydantic import BaseModel

from services.llm.openai.parse_engine import OpenaiAddressParser

parser_router = APIRouter(prefix='/parser')


class AddressParseRequest(BaseModel):
    address: str

@parser_router.post('/address', response_model=Dict)
def openai_address_parser(body: AddressParseRequest) -> Dict:
    address = body.address
    service = OpenaiAddressParser()
    return service.parse(address)


@parser_router.post('/address-test', response_model=Dict)
def openai_address_parser(body: AddressParseRequest) -> Dict:
    # service = OpenaiAddressParser()
    return {
  "name1": "Mustermann",
  "name2": "Mustermann GMBH",
  "name3": "6 Stock",
  "street1": "Fehrfeld 88",
  "zipCode": "28203",
  "city": "Bremen",
  "province": "Bremen",
  "country": "DE",
  "email": "mustermann@example.com",
  "telephone": "",
  "mobile": "15357532400"
}