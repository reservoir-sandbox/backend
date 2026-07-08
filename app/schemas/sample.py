from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import Status


class SampleRead(BaseModel):
    id: int
    size: int
    sha256: str
    object_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SampleListItem(BaseModel):
    sample_id: int
    filename: str
    uploaded_at: datetime
    current_job_id: int | None
    current_job_status: Status | None
    engine_version: str | None
    analysis_stale: bool | None
