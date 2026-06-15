from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health_router, v1_router
from app.api.middlewares import limiter
from app.core import API_V1_PREFIX, get_settings
from app.exceptions import register_exception_handlers
from app.lifespan import lifespan

settings = get_settings()

app = FastAPI(
    title="My Auth API",
    version="1.0.1",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.state.limiter = limiter
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(v1_router, prefix=API_V1_PREFIX)
