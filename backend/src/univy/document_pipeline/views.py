from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import Literal, List, Optional, Annotated
from pydantic import BaseModel, Field
import os
from pathlib import Path
import shutil
from loguru import logger

from univy.constants import UPLOAD_DIR
from univy.document_pipeline.tasks import parse_pdf_and_ingest_to_rag, scan_for_new_files, cleanup_old_task_directories
from univy.celery_config.celery_univy import app
from univy.auth.security import JWT

router = APIRouter(prefix="/document_pipeline", tags=["document_pipeline"])


class DocumentManager:
    def __init__(self, input_dir: str, supported_extensions: tuple = (
        ".txt", ".pdf", ".md"
    )):
        self.input_dir = Path(input_dir)
        self.supported_extensions = supported_extensions
        self.input_dir.mkdir(parents=True, exist_ok=True)

        self.indexed_files = set()

    def scan_dir_for_new_files(self) -> List[Path]:
        new_files = []
        for ext in self.supported_extensions:
            logger.debug(f"Scanning for new files with extension {ext}")
            for file_path in self.input_dir.rglob(f"*{ext}"):
                if file_path not in self.indexed_files:
                    new_files.append(file_path)
        return new_files

    def mark_file_as_indexed(self, file_path: Path):
        self.indexed_files.add(file_path)

    def is_supported_file(self, filename: str) -> bool:
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)


class InsertResponse(BaseModel):
    status: Literal["success", "duplicated", "partial_success",
                    "failure"] = Field(description="Status of the insertion")
    message: str = Field(description="Message of the insertion")
    task_id: Optional[str] = Field(
        None, description="Celery task ID for tracking")
    file_name: Optional[str] = Field(
        None, description="Name of the file being processed")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "File 'document.pdf' uploaded successfully. Processing will continue in the background."
            }
        }


class ScanResponse(BaseModel):
    status: Literal["success", "failure"] = Field(
        description="Status of the scan")
    message: str = Field(description="Message of the scan")
    task_id: Optional[str] = Field(
        None, description="Celery task ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Scan completed successfully",
                "task_id": "abc123-def456-ghi789"
            }
        }


# TODO: Add another dependency file later and change to S3
document_manager = DocumentManager(UPLOAD_DIR)


@router.post("/scan", response_model=ScanResponse)
async def scan_for_new_files_endpoint(jwt: Annotated[str, Depends(JWT)], user_id: Optional[int] = None):
    """Scan for new files using Celery"""

    try:
        # Start the Celery task
        task = scan_for_new_files.delay(user_id)

        return ScanResponse(
            status="success",
            message="File scan started successfully. Check task status for results.",
            task_id=task.id
        )
    except Exception as e:
        logger.error(f"Error starting file scan: {e}")
        return ScanResponse(
            status="failure",
            message=f"Failed to start file scan: {str(e)}"
        )


@router.post("/upload", response_model=InsertResponse)
async def upload_pdf(file: UploadFile = File(...)):
    # TODO: Implement the upload logic
    try:
        file_path = document_manager.input_dir / file.filename
        if file_path.exists():
            return InsertResponse(status="duplicated", message=f"File '{file.filename}' already exists in the upload directory.")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Start the parsing task and get the task ID
        task = parse_pdf_and_ingest_to_rag.delay(file.filename)

        return InsertResponse(
            status="success",
            message=f"File '{file.filename}' uploaded successfully. Processing will continue in the background.",
            task_id=task.id,
            file_name=file.filename
        )
    except Exception as e:
        return InsertResponse(status="failure", message=f"Failed to upload file '{file.filename}': {str(e)}")


@router.get("/status")
async def get_processing_status(file_name: str):
    """Get the status of a file being processed"""

    try:
        result = app.AsyncResult(file_name)
        return {
            "file_name": file_name,
            "status": result.status,
            "result": result.result if result.ready() else None
        }
    except Exception as e:
        logger.error(f"Error getting status for {file_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a Celery task"""
    try:
        result = app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_directories(days_old: int = 7):
    """Clean up old task directories"""
    try:
        task = cleanup_old_task_directories.delay(days_old)
        return {
            "status": "success",
            "message": f"Cleanup task started for directories older than {days_old} days",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error starting cleanup task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start cleanup: {str(e)}")


pdf_parser_router = router
