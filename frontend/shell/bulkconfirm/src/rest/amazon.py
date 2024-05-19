
import requests

class Orders:
    def __init__(self, base_url):
        self.base_url = f"{base_url}/orders"

    def unshipped_order_ids(self):
        url = f"{self.base_url}/unshipped"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to get unshipped order ids. Status code: {response.status_code}")

    def get_seller_central_urls(self):
        url = f"{self.base_url}/sc-urls"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to get seller central urls. Status code: {response.status_code}")

    def parsePackSlip(self, content, country="DE", formatIn="html",
                      formatOut=""):
        url = f"{self.base_url}/packslip/parse"
        body = {
            "data": content,
            "country": country,
            "formatIn": formatIn,
            "formatOut": formatOut
        }
        response = requests.post(url, json=body)
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to parse packslip. Status code: {response.status_code}")

