from fastapi import Depends

from app.core import Settings, get_settings
from app.crud import JobCRUD, JobTaskCRUD, SampleCRUD, UserCRUD, UserSampleCRUD
from app.db import S3Client, get_s3_client
from app.services import (
    AuthService,
    JobService,
    SampleService,
    StorageService,
    UserService,
)

from .repositories import (
    get_job_crud,
    get_job_task_crud,
    get_sample_crud,
    get_user_crud,
    get_user_sample_crud,
)


async def get_user_service(user_crud: UserCRUD = Depends(get_user_crud)):
    return UserService(user_crud)


async def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    settings: Settings = Depends(get_settings),
):
    return AuthService(user_service, settings)


async def get_storage_service(s3_client: S3Client = Depends(get_s3_client)):
    return StorageService(s3_client)


async def get_job_service(
    job_crud: JobCRUD = Depends(get_job_crud),
    job_task_crud: JobTaskCRUD = Depends(get_job_task_crud),
):
    return JobService(job_crud, job_task_crud)


async def get_sample_service(
    storage_service: StorageService = Depends(get_storage_service),
    job_service: JobService = Depends(get_job_service),
    sample_crud: SampleCRUD = Depends(get_sample_crud),
    user_sample_crud: UserSampleCRUD = Depends(get_user_sample_crud),
    settings: Settings = Depends(get_settings),
):
    return SampleService(
        storage_service, job_service, sample_crud, user_sample_crud, settings
    )
