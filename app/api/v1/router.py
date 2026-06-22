from fastapi import APIRouter

from .endpoints import auth_router, samples_router, users_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(samples_router)
