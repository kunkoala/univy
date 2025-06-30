from fastapi import APIRouter
from univy.document_pipeline.views import router as document_pipeline_router
from univy.rag.views import router as rag_router

api_router = APIRouter()

api_router.include_router(document_pipeline_router)
api_router.include_router(rag_router)
