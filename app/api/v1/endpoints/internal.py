from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, get_job_service, verify_worker_token
from app.schemas import TaskCallback
from app.services import JobService

router = APIRouter()


@router.post("/tasks/{task_id:int}/callback", status_code=204)
async def task_callback(
    task_id: int,
    payload: TaskCallback,
    _=Depends(verify_worker_token),
    session: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
):
    await service.apply_task_result(
        session,
        task_id=task_id,
        status=payload.status,
        report_object_name=payload.report_object_name,
        result=payload.result,
        error=payload.error,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
    )
