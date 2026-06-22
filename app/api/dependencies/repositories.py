from app.crud import JobCRUD, JobTaskCRUD, SampleCRUD, UserCRUD, UserSampleCRUD


async def get_user_crud():
    return UserCRUD()


async def get_sample_crud():
    return SampleCRUD()


async def get_user_sample_crud():
    return UserSampleCRUD()


async def get_job_crud():
    return JobCRUD()


async def get_job_task_crud():
    return JobTaskCRUD()
