from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.ycode.core.config import settings
from src.ycode.api.v1.auth.routes import auth_router


app = FastAPI(
    title="Ycode API",
    description="API for Ycode application",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])