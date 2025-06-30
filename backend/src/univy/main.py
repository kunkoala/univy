from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os


# import sentry_sdk
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from univy.config import app_configs, settings
from univy.api import api_router
from univy.constants import UPLOAD_DIR, OUTPUT_DIR

# TEMPORARY SOLUTION TO UPLOAD FILES LOCALLY, LATER ON CHANGE TO AWS S3
# Each user has their own S3 bucket, so we need to create a directory for each user
# to upload their files
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    # Startup
    yield
    # Shutdown


app = FastAPI(**app_configs, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

# if settings.ENVIRONMENT.is_deployed:
#     sentry_sdk.init(
#         dsn=settings.SENTRY_DSN,
#         environment=settings.ENVIRONMENT,
#     )

app.include_router(api_router)


@app.get("/healthcheck", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
