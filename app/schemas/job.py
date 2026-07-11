from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.enums import Status, TaskType


class JobRead(BaseModel):
    id: int
    sample_id: int
    engine_version: str
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
    report_object_name: str | None
    result: dict | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None

    model_config = ConfigDict(from_attributes=True)


class JobDetails(JobRead):
    tasks: list[JobTaskRead]


class TaskCallback(BaseModel):
    status: Status
    report_object_name: str | None = None
    result: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, st: Status) -> Status:
        if st not in {Status.COMPLETED, Status.FAILED}:
            raise ValueError("Status must be COMPLETED or FAILED")
        return st
