import httpx
from core.log import logger


class GlsEuApiClient:
    def __init__(self, base_url: str, headers: dict):
        self.base_url = base_url.rstrip("/")
        self.headers = headers

    async def create_shipment(self, body: dict) -> dict:
        url = f"{self.base_url}/shipments"
        logger.info(f"[GLS API] POST {url} | body={body}")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=body, headers=self.headers)
        if resp.status_code not in (200, 201):
            logger.error(f"GLS create shipment failed: {resp.status_code} | {resp.text}")
            raise Exception(f"GLS API Error {resp.status_code}: {resp.text}")
        logger.info(f"GLS label successfully created: {resp.status_code}")
        return resp.json()

    async def get_tracking_status(self, tracking_number: str) -> dict:
        url = f"{self.base_url}/tracking/references/{tracking_number}"
        logger.info(f"[GLS API] GET {url}")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self.headers)
        if resp.status_code not in (200, 201):
            logger.error(f"GLS get tracking status failed: {resp.status_code} | {resp.text}")
            raise Exception(f"GLS API Error {resp.status_code}: {resp.text}")
        logger.info(f"GLS tracking status successfully retrieved: {resp.status_code}")
        return resp.json()

