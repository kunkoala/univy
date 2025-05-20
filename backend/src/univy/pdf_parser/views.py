from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from .service import process_pdf_upload
from univy.lightrag_client import LightRAGClient
from typing import Dict
import uuid

router = APIRouter(prefix="/pdf_parser", tags=["pdf_parser"])

# In-memory status store (for demo; use Redis or DB for production)
processing_status_store: Dict[str, Dict] = {}

def get_lightrag_client():
    return LightRAGClient()  # Uses config by default

@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    lightrag_client: LightRAGClient = Depends(get_lightrag_client),
):
    process_id = str(uuid.uuid4())
    processing_status_store[process_id] = {"status": "processing", "message": "File is being processed."}
    file_content = await file.read()
    filename = file.filename
    background_tasks.add_task(process_and_upload, file_content, filename, lightrag_client, process_id)
    return {"status": "processing_started", "process_id": process_id, "message": "Processing started in background."}

async def process_and_upload(file_content: bytes, filename: str, lightrag_client: LightRAGClient, process_id: str):
    try:
        result = await process_pdf_upload(file_content, filename, lightrag_client)
        processing_status_store[process_id] = {"status": result.get("status", "unknown"), "message": result.get("message", "Done")}
    except Exception as e:
        processing_status_store[process_id] = {"status": "error", "message": str(e)}

@router.get("/processing_status/{process_id}")
async def get_processing_status(process_id: str):
    status = processing_status_store.get(process_id)
    if not status:
        raise HTTPException(status_code=404, detail="Process ID not found.")
    return status

@router.get("/pipeline_status")
async def pipeline_status(lightrag_client: LightRAGClient = Depends(get_lightrag_client)):
    result = await lightrag_client.get_pipeline_status()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Pipeline status error"))
    return result

pdf_parser_router = router
