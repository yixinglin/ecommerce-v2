from datetime import timezone, datetime
from pydantic import BaseModel


class UTCModel(BaseModel):
    @classmethod
    def __get_validators__(cls):
        yield cls.ensure_utc

    @staticmethod
    def ensure_utc(v):
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        }