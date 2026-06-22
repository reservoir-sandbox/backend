from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SampleRead(BaseModel):
    id: int
    size: int
    sha256: str
    object_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
