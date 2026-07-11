from typing import cast

from fastapi import Request

from app.services import JobLauncher


def get_job_launcher(request: Request) -> JobLauncher:
    return cast(JobLauncher, request.app.state.job_launcher)
