import json
import os
from datetime import datetime
from core.config import settings
from pydantic import BaseModel

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'

def now():
    return datetime.now().strftime(DATETIME_PATTERN)


def today():
    return datetime.now().date()


# This class represents the Amazon Sp API keys and provides methods to fetch orders and order items
class AmazonSpAPIKey(BaseModel):
    def __init__(self):
        self.refresh_token: str
        self.lwa_app_id: str
        self.lwa_client_secret: str
        self.aws_access_key: str
        self.aws_secret_key: str
        self.role_arn: str

    @classmethod
    def from_json(cls):
        # Load the API keys from the JSON file
        file_path = os.path.join('conf', 'apikeys',
                                 settings.AMAZON_ACCESS_KEY)
        with open(file_path, 'r') as fp:
            data = json.load(fp)
        k = AmazonSpAPIKey()
        k.__dict__.update(data)
        return k