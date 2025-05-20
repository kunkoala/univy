from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from .service import process_pdf_upload
from univy.lightrag_client import LightRAGClient

router = APIRouter(prefix="/pdf_parser", tags=["pdf_parser"])

def get_lightrag_client():
    return LightRAGClient()  # Uses config by default

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    lightrag_client: LightRAGClient = Depends(get_lightrag_client),
):
    result = await process_pdf_upload(file, lightrag_client)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Upload error"))
    return result

@router.get("/pipeline_status")
async def pipeline_status(lightrag_client: LightRAGClient = Depends(get_lightrag_client)):
    result = await lightrag_client.get_pipeline_status()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Pipeline status error"))
    return result

pdf_parser_router = router
