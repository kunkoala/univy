from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

from univy.celery_config.celery_univy import app
from univy.pdf_parser.constants import UPLOAD_DIR

import json
import time
import os
from pathlib import Path

from loguru import logger


from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from univy.pdf_parser.constants import UPLOAD_DIR, OUTPUT_DIR

from univy.celery_config.celery_univy import app


# TEMPORARY SOLUTION TO UPLOAD FILES LOCALLY, LATER ON CHANGE TO AWS S3
# Each user has their own S3 bucket, so we need to create a directory for each user
# to upload their files
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.task(bind=True)
def parse_pdf(self, pdf_file_name, do_ocr=False, use_gpu=False, text_output=False, markdown_output=True, doctags_output=True, json_output=True):
    logger.info(f"Parsing PDF file: {pdf_file_name}")

    try:
        input_doc_path = Path(UPLOAD_DIR) / pdf_file_name
        if not input_doc_path.exists():
            raise FileNotFoundError(
                f"File {pdf_file_name} not found in {UPLOAD_DIR}")

        # Create task-specific output directory
        task_id = self.request.id
        task_output_dir = Path(OUTPUT_DIR) / f"task_{task_id}"
        task_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created output directory: {task_output_dir}")

        # Docling Parse with EasyOCR
        # ----------------------
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = do_ocr
        pipeline_options.ocr_options.use_gpu = use_gpu
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=4, device=AcceleratorDevice.AUTO
        )

        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options)
            }
        )

        ###########################################################################
        # Convert PDF to document
        ###########################################################################

        start_time = time.time()
        conv_result = doc_converter.convert(input_doc_path)
        end_time = time.time() - start_time

        logger.info(f"Document converted in {end_time:.2f} seconds.")

        # Export results to task-specific directory
        doc_filename = conv_result.input.file.stem
        generated_files = []

        # Export Deep Search document JSON format:
        if json_output:
            json_file = task_output_dir / f"{doc_filename}.json"
            with json_file.open("w", encoding="utf-8") as fp:
                fp.write(json.dumps(conv_result.document.export_to_dict()))
            generated_files.append(str(json_file))

        # Export Text format:
        if text_output:
            txt_file = task_output_dir / f"{doc_filename}.txt"
            with txt_file.open("w", encoding="utf-8") as fp:
                fp.write(conv_result.document.export_to_text())
            generated_files.append(str(txt_file))

        # Export Markdown format:
        if markdown_output:
            md_file = task_output_dir / f"{doc_filename}.md"
            with md_file.open("w", encoding="utf-8") as fp:
                fp.write(conv_result.document.export_to_markdown())
            generated_files.append(str(md_file))

        # Export Document Tags format:
        if doctags_output:
            doctags_file = task_output_dir / f"{doc_filename}.doctags"
            with doctags_file.open("w", encoding="utf-8") as fp:
                fp.write(conv_result.document.export_to_doctags())
            generated_files.append(str(doctags_file))

        return {
            "status": "success",
            "message": f"PDF parsing completed for {pdf_file_name}",
            "task_id": task_id,
            "output_directory": str(task_output_dir),
            "generated_files": generated_files,
            "processing_time": end_time,
            "original_file": pdf_file_name
        }

    except Exception as e:
        logger.error(f"Error parsing PDF {pdf_file_name}: {e}")
        return {
            "status": "error",
            "message": f"Failed to parse PDF {pdf_file_name}: {str(e)}",
            "task_id": self.request.id if hasattr(self, 'request') else None,
            "original_file": pdf_file_name
        }


@app.task(bind=True)
def scan_for_new_files(self, user_id: int = None) -> Dict[str, Any]:
    """Scan upload directory for new files"""
    logger.info("Starting file scan")

    upload_path = Path(UPLOAD_DIR)
    supported_extensions = (".txt", ".pdf", ".md")

    new_files = []
    for ext in supported_extensions:
        for file_path in upload_path.rglob(f"*{ext}"):
            new_files.append(str(file_path))

    logger.info(f"Found {len(new_files)} files: {new_files}")

    return {
        "status": "success",
        "message": f"Found {len(new_files)} files",
        "files": new_files,
        "user_id": user_id
    }


@app.task(bind=True)
def scan_for_new_files(self, user_id: int = None) -> Dict[str, Any]:
    """Scan upload directory for new files"""
    logger.info("Starting file scan")

    upload_path = Path(UPLOAD_DIR)
    supported_extensions = (".txt", ".pdf", ".md")

    new_files = []
    for ext in supported_extensions:
        for file_path in upload_path.rglob(f"*{ext}"):
            new_files.append(str(file_path))

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
    import time
    from datetime import datetime, timedelta

    logger.info(f"Cleaning up task directories older than {days_old} days")

    output_path = Path(OUTPUT_DIR)
    cutoff_time = datetime.now() - timedelta(days=days_old)
    cutoff_timestamp = cutoff_time.timestamp()

    cleaned_dirs = []
    failed_dirs = []

    for task_dir in output_path.iterdir():
        if task_dir.is_dir() and task_dir.name.startswith("task_"):
            try:
                # Check if directory is old enough
                dir_mtime = task_dir.stat().st_mtime
                if dir_mtime < cutoff_timestamp:
                    # Remove the entire task directory
                    import shutil
                    shutil.rmtree(task_dir)
                    cleaned_dirs.append(str(task_dir))
                    logger.info(f"Cleaned up old task directory: {task_dir}")
            except Exception as e:
                failed_dirs.append((str(task_dir), str(e)))
                logger.error(f"Failed to clean up {task_dir}: {e}")

    return {
        "status": "success",
        "message": f"Cleanup completed. Removed {len(cleaned_dirs)} directories.",
        "cleaned_directories": cleaned_dirs,
        "failed_directories": failed_dirs
    }
