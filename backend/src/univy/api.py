from fastapi import APIRouter
from univy.pdf_parser.views import router as pdf_parser_router
from univy.celery.views import router as celery_router

api_router = APIRouter()

api_router.include_router(pdf_parser_router)
api_router.include_router(celery_router)
