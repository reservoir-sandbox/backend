from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import Status, TaskType


class JobRead(BaseModel):
    id: int
    sample_id: int
    status: Status
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class JobTaskRead(BaseModel):
    id: int
    job_id: int
    task_type: TaskType
    status: Status
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None

    model_config = ConfigDict(from_attributes=True)


class JobDetails(JobRead):
    tasks: list[JobTaskRead]
