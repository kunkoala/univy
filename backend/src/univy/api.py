from fastapi import APIRouter
from univy.pdf_parser.views import pdf_parser_router

api_router = APIRouter()

api_router.include_router(pdf_parser_router)
