from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import asyncio

from univy.celery_config.celery_univy import app
from univy.constants import UPLOAD_DIR, OUTPUT_DIR
from univy.document_pipeline.utils import (
    validate_pdf_file,
    create_task_output_directory,
    convert_pdf_to_markdown,
    read_markdown_content,
    ingest_text_to_lightrag,
    scan_directory_for_files,
    cleanup_old_directories
)


@app.task(bind=True)
def parse_pdf_and_ingest_to_rag(self, pdf_file_name, do_ocr=False, use_gpu=False):
    """
    Parse PDF to markdown and automatically ingest into LightRAG.
    This combines PDF parsing and RAG ingestion in a single workflow.
    """
    logger.info(f"Starting PDF parsing and RAG ingestion for: {pdf_file_name}")

    try:
        # Step 1: Validate and get PDF file path
        input_doc_path = validate_pdf_file(pdf_file_name)

        # Step 2: Create task-specific output directory
        task_output_dir = create_task_output_directory(self.request.id)

        # Step 3: Convert PDF to markdown
        md_file, processing_time = convert_pdf_to_markdown(
            pdf_path=input_doc_path,
            output_dir=task_output_dir,
            do_ocr=do_ocr,
            use_gpu=use_gpu,
            retry_with_ocr=True
        )

        # Step 4: Read markdown content
        markdown_text = read_markdown_content(md_file)

        # Step 5: Ingest into LightRAG
        asyncio.run(ingest_text_to_lightrag(markdown_text, pdf_file_name))

        logger.info(f"Document processing completed in {processing_time:.2f} seconds.")
        return {
            "status": "success",
            "message": f"PDF {pdf_file_name} parsed and ingested into LightRAG successfully",
            "task_id": self.request.id,
            "pdf_file": pdf_file_name,
            "markdown_file": str(md_file),
            "processing_time": processing_time
        }

    except Exception as e:
        logger.error(f"Error in parse_pdf_and_ingest_to_rag for {pdf_file_name}: {e}")
        return {
            "status": "error",
            "message": f"Failed to process PDF {pdf_file_name}: {str(e)}",
            "task_id": self.request.id if hasattr(self, 'request') else None,
            "original_file": pdf_file_name
        }


@app.task(bind=True)
def scan_for_new_files(self, user_id: int = None) -> Dict[str, Any]:
    """Scan upload directory for new files"""
    logger.info("Starting file scan")

    upload_path = Path(UPLOAD_DIR)
    supported_extensions = (".txt", ".pdf", ".md")
    
    new_files = scan_directory_for_files(upload_path, supported_extensions)

    logger.info(f"Found {len(new_files)} files: {new_files}")

    return {
        "status": "success",
        "message": f"Found {len(new_files)} files",
        "files": new_files,
        "user_id": user_id
    }


@app.task(bind=True)
def cleanup_old_task_directories(self, days_old: int = 7) -> Dict[str, Any]:
    """Clean up task directories older than specified days"""
    logger.info(f"Cleaning up task directories older than {days_old} days")

    output_path = Path(OUTPUT_DIR)
    cleaned_dirs, failed_dirs = cleanup_old_directories(output_path, days_old)

    return {
        "status": "success",
        "message": f"Cleanup completed. Removed {len(cleaned_dirs)} directories.",
        "cleaned_directories": cleaned_dirs,
        "failed_directories": failed_dirs
    }
