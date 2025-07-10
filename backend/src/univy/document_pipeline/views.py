from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import Literal, List, Optional, Annotated
from pydantic import BaseModel, Field
import os
from pathlib import Path
import shutil
from loguru import logger

from univy.constants import UPLOAD_DIR
from univy.document_pipeline.tasks import pipeline_process_pdf, scan_for_new_files, cleanup_all_task_directories
from univy.celery_config.celery_univy import app
from univy.auth.security import get_current_user

router = APIRouter(prefix="/document_pipeline", tags=["document_pipeline"])


def sanitize_filename(filename: str, input_dir: Path) -> str:
    """
    Sanitize uploaded filename to prevent Path Traversal attacks.

    Args:
        filename: The original filename from the upload
        input_dir: The target input directory

    Returns:
        str: Sanitized filename that is safe to use

    Raises:
        HTTPException: If the filename is unsafe or invalid
    """
    # Basic validation
    if not filename or not filename.strip():
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    # Remove path separators and traversal sequences
    clean_name = filename.replace("/", "").replace("\\", "")
    clean_name = clean_name.replace("..", "")

    # Remove control characters and null bytes
    clean_name = "".join(c for c in clean_name if ord(c) >= 32 and c != "\x7f")

    # Remove leading/trailing whitespace and dots
    clean_name = clean_name.strip().strip(".")

    # Check if anything is left after sanitization
    if not clean_name:
        raise HTTPException(
            status_code=400, detail="Invalid filename after sanitization"
        )

    # Verify the final path stays within the input directory
    try:
        final_path = (input_dir / clean_name).resolve()
        if not final_path.is_relative_to(input_dir.resolve()):
            raise HTTPException(
                status_code=400, detail="Unsafe filename detected")
    except (OSError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid filename")

    return clean_name


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
async def scan_for_new_files_endpoint(user: Annotated[str, Depends(get_current_user)]):
    """Scan for new files using Celery"""

    try:
        # Start the Celery task
        task = scan_for_new_files.delay(user.id)

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
async def upload_pdf(user: Annotated[str, Depends(get_current_user)], file: UploadFile = File(...)):
    # TODO: Implement the upload logic
    try:
        safe_filename = sanitize_filename(
            file.filename, document_manager.input_dir)

        if not document_manager.is_supported_file(safe_filename):
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {file.filename}")

        file_path = document_manager.input_dir / safe_filename

        if file_path.exists():
            return InsertResponse(status="duplicated", message=f"File '{file.filename}' already exists in the upload directory.")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Start the parsing task and get the task ID
        task = pipeline_process_pdf.delay(file.filename)

        return InsertResponse(
            status="success",
            message=f"File '{file.filename}' uploaded successfully. Processing will continue in the background.",
            task_id=task.id,
            file_name=file.filename
        )
    except Exception as e:
        return InsertResponse(status="failure", message=f"Failed to upload file '{file.filename}': {str(e)}")


@router.get("/status")
async def get_processing_status(file_name: str, user: Annotated[str, Depends(get_current_user)]):
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
async def get_task_status(task_id: str, user: Annotated[str, Depends(get_current_user)]):
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
async def cleanup_all_directories_endpoint(user: Annotated[str, Depends(get_current_user)]):
    """Delete all files and directories in OUTPUT_DIR and UPLOAD_DIR"""
    try:
        task = cleanup_all_task_directories.delay()
        return {
            "status": "success",
            "message": f"Cleanup task started for all files and directories in OUTPUT_DIR and UPLOAD_DIR",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error starting cleanup task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start cleanup: {str(e)}"
        )


pdf_parser_router = router
