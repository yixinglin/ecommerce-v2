from typing import List

import requests

class GlsShipment:

    def __init__(self, base_url):
        self.base_url = f"{base_url}/gls/shipments"

    def bulk_create_shipments(self, shipments: List[dict]):
        url = f"{self.base_url}/bulk"
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, json=shipments)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to create shipments: {response.text}")


    def get_bulk_ship_labels(self, refs: List[str]):
        url = f"{self.base_url}/bulk-labels"
        headers = {'Content-Type': 'application/json'}
        references = ";".join(refs)
        params = {"refs": references}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Failed to get shipment labels: {response.text}")

    def get_pick_pack_slip(self, refs: List[str]):
        url = f"{self.base_url}/report"
        references = ";".join(refs)
        params = {"refs": references}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Failed to get pick-pack slips: {response.text}")

    def get_pick_items(self, refs: List[str]):
        url = f"{self.base_url}/pick"
        headers = {'Content-Type': 'application/json'}
        references = ";".join(refs)
        params = {"refs": references}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get pick items: {response.text}")



