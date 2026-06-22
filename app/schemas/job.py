from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import Status


class JobRead(BaseModel):
    id: int
    sample_id: int
    status: Status
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
