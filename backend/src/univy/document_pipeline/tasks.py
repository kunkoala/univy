from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import asyncio

from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import time
import json

from univy.celery_config.celery_univy import app
from univy.constants import UPLOAD_DIR, OUTPUT_DIR, RAG_DIR
from univy.document_pipeline.utils import scan_directory_for_files, cleanup_all_directories, ingest_texts_to_lightrag, export_documents, save_document_metadata_to_db


@app.task(bind=True)
def pipeline_process_pdf(self, pdf_file_names: List[str], user_id: int, do_ocr=False, use_gpu=False, markdown_output=True, doctags_output=True, json_output=True, num_threads=4):
    logger.info(f"=== PARSING PDF FILES ===")

    # Create task-specific output directory
    task_id = self.request.id
    task_output_dir = Path(OUTPUT_DIR) / f"task_{task_id}"
    task_output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created task-specific output directory {task_output_dir}")

    input_doc_paths = [
        Path(UPLOAD_DIR) / pdf_file_name for pdf_file_name in pdf_file_names]

    logger.info(f"Parsing PDF files: {input_doc_paths}")

    try:
        for input_doc_path in input_doc_paths:
            if not input_doc_path.exists():
                raise FileNotFoundError(
                    f"File {input_doc_path} not found in {UPLOAD_DIR}")

        # Docling Parse with EasyOCR
        # ----------------------
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = do_ocr
        pipeline_options.ocr_options.use_gpu = use_gpu
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=num_threads, device=AcceleratorDevice.AUTO
        )
        pipeline_options.generate_page_images = True

        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options, backend=DoclingParseV4DocumentBackend)
            }
        )

        ###########################################################################
        # Convert PDF to document
        ###########################################################################

        start_time = time.time()
        conv_result = doc_converter.convert_all(
            input_doc_paths, raises_on_error=False)  # let conversion run through all files

        success_count, partial_success_count, failure_count, generated_files, converted_texts_lightrag_input, converted_file_paths, doc_ids = export_documents(
            conv_result, task_output_dir, markdown_output=markdown_output, doctags_output=doctags_output, json_output=json_output)

        logger.info(
            f"converted_texts_lightrag_input: {converted_texts_lightrag_input}")

        end_time = time.time() - start_time

        logger.info(f"Document converted in {end_time:.2f} seconds.")

        ingest_time = time.time()
        # Ingest text to LightRAG
        logger.info(
            f"Ingesting {len(converted_texts_lightrag_input)} texts to LightRAG")

        asyncio.run(ingest_texts_to_lightrag(
            converted_texts_lightrag_input, converted_file_paths, doc_ids))

        ingest_time = time.time() - ingest_time
        logger.info(
            f"Ingested texts to LightRAG in {ingest_time:.2f} seconds.")

        # Save document metadata to database
        processing_results = {
            "success_count": success_count,
            "partial_success_count": partial_success_count,
            "failure_count": failure_count,
            "generated_files": generated_files
        }
        
        documents = asyncio.run(save_document_metadata_to_db(
            user_id=user_id,
            doc_ids=doc_ids,
            file_paths=converted_file_paths,
            processing_results=processing_results,
            task_id=task_id,
            processing_time=end_time,
            ingest_time=ingest_time
        ))

        # Trigger smart notes generation for each document
        from univy.smart_notes.tasks import generate_smart_notes_task
        for doc_id in doc_ids:
            generate_smart_notes_task.delay(doc_id, user_id)

        return {
            "status": "success",
            "doc_ids": doc_ids,
            "documents": [{"doc_id": doc.doc_id, "title": doc.title, "status": doc.processing_status} for doc in documents],
            "message": f"PDF parsing completed for {pdf_file_names}",
            "task_id": task_id,
            "output_directory": str(task_output_dir),
            "processing_time": end_time,
            "processing_results": {
                "success_count": success_count,
                "partial_success_count": partial_success_count,
                "failure_count": failure_count
            },
            "generated_files": generated_files,
            "original_file": pdf_file_names
        }

    except Exception as e:
        logger.error(f"Error parsing PDF {pdf_file_names}: {e}")
        return {
            "status": "error",
            "message": f"Failed to parse PDF {pdf_file_names}: {str(e)}",
            "task_id": self.request.id if hasattr(self, 'request') else None,
            "original_file": pdf_file_names
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
def cleanup_all_task_directories(self) -> Dict[str, Any]:
    """Delete all files and directories in OUTPUT_DIR, UPLOAD_DIR, and RAG_DIR"""
    logger.info(
        f"Cleaning up all files and directories in OUTPUT_DIR, UPLOAD_DIR, and RAG_DIR")

    output_deleted, output_failed = cleanup_all_directories(Path(OUTPUT_DIR))
    upload_deleted, upload_failed = cleanup_all_directories(Path(UPLOAD_DIR))
    rag_deleted, rag_failed = cleanup_all_directories(Path(RAG_DIR))

    return {
        "status": "success",
        "message": f"Cleanup completed.",
        "output_deleted": output_deleted,
        "output_failed": output_failed,
        "upload_deleted": upload_deleted,
        "upload_failed": upload_failed,
        "rag_deleted": rag_deleted,
        "rag_failed": rag_failed
    }
