import os
import asyncio
import time
import unicodedata
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from lightrag import LightRAG
from lightrag.llm.openai import openai_embed, openai_complete_if_cache
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger
from dotenv import load_dotenv

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from univy.config import settings
from univy.constants import UPLOAD_DIR, OUTPUT_DIR

setup_logger("lightrag", level="INFO")

WORKING_DIR = "./rag_storage"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for processing (handle non-ASCII characters).
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for file operations
    """
    # Normalize unicode characters and remove/replace problematic ones
    sanitized = unicodedata.normalize('NFD', filename)
    sanitized = re.sub(r'[^\w\s\-\.]', '_', sanitized)
    sanitized = sanitized.replace(' ', '_')
    return sanitized


def create_task_output_directory(task_id: str) -> Path:
    """
    Create task-specific output directory.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Path to the created output directory
    """
    task_output_dir = Path(OUTPUT_DIR) / f"task_{task_id}"
    task_output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory: {task_output_dir}")
    return task_output_dir


def setup_docling_converter(do_ocr: bool = False, use_gpu: bool = False) -> DocumentConverter:
    """
    Set up Docling document converter with specified options.
    
    Args:
        do_ocr: Whether to enable OCR
        use_gpu: Whether to use GPU for OCR
        
    Returns:
        Configured DocumentConverter instance
    """
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
    
    return doc_converter


def convert_pdf_to_markdown(
    pdf_path: Path, 
    output_dir: Path, 
    do_ocr: bool = False, 
    use_gpu: bool = False,
    retry_with_ocr: bool = True
) -> Tuple[Path, float]:
    """
    Convert PDF to markdown format.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the markdown file
        do_ocr: Whether to enable OCR
        use_gpu: Whether to use GPU for OCR
        retry_with_ocr: Whether to retry with OCR if conversion fails
        
    Returns:
        Tuple of (markdown_file_path, processing_time)
        
    Raises:
        Exception: If PDF conversion fails
    """
    start_time = time.time()
    
    try:
        doc_converter = setup_docling_converter(do_ocr, use_gpu)
        conv_result = doc_converter.convert(pdf_path)
        logger.info(f"Document converted successfully")
        
    except Exception as pdf_error:
        logger.error(f"PDF conversion failed: {pdf_error}")
        
        # Try with OCR enabled if it wasn't already and retry is allowed
        if not do_ocr and retry_with_ocr:
            logger.info("Retrying with OCR enabled...")
            doc_converter = setup_docling_converter(do_ocr=True, use_gpu=use_gpu)
            conv_result = doc_converter.convert(pdf_path)
            logger.info(f"Document converted with OCR")
        else:
            raise pdf_error

    # Export markdown format
    doc_filename = conv_result.input.file.stem
    md_file = output_dir / f"{doc_filename}.md"
    
    with md_file.open("w", encoding="utf-8") as fp:
        fp.write(conv_result.document.export_to_markdown())

    processing_time = time.time() - start_time
    logger.info(f"Markdown file created: {md_file} in {processing_time:.2f} seconds")
    
    return md_file, processing_time


def read_markdown_content(md_file: Path) -> str:
    """
    Read markdown content from file.
    
    Args:
        md_file: Path to the markdown file
        
    Returns:
        Content of the markdown file
    """
    with open(md_file, "r", encoding="utf-8") as file:
        content = file.read()
    
    logger.info(f"Read markdown content from: {md_file}")
    return content


async def ingest_text_to_lightrag(text: str, source_file: str) -> None:
    """
    Ingest text content into LightRAG.
    
    Args:
        text: Text content to ingest
        source_file: Source file name for metadata
        
    Raises:
        Exception: If ingestion fails
    """
    rag = None
    try:
        rag = await initialize_lightrag()
        await rag.apipeline_enqueue_documents(
            input=[text],
            file_paths=[source_file]
        )
        await rag.apipeline_process_enqueue_documents()
        logger.info(f"Successfully ingested {source_file} into LightRAG")
    except Exception as e:
        logger.error(f"Error ingesting to LightRAG: {e}")
        raise
    finally:
        if rag:
            await rag.finalize_storages()


def validate_pdf_file(pdf_file_name: str) -> Path:
    """
    Validate that PDF file exists and return its path.
    
    Args:
        pdf_file_name: Name of the PDF file
        
    Returns:
        Path to the PDF file
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    input_doc_path = Path(UPLOAD_DIR) / pdf_file_name
    if not input_doc_path.exists():
        raise FileNotFoundError(f"File {pdf_file_name} not found in {UPLOAD_DIR}")
    return input_doc_path


def scan_directory_for_files(directory: Path, extensions: tuple = (".txt", ".pdf", ".md")) -> list:
    """
    Scan directory for files with specified extensions.
    
    Args:
        directory: Directory to scan
        extensions: Tuple of file extensions to look for
        
    Returns:
        List of file paths found
    """
    files = []
    for ext in extensions:
        for file_path in directory.rglob(f"*{ext}"):
            files.append(str(file_path))
    return files


def cleanup_old_directories(base_dir: Path, days_old: int) -> Tuple[list, list]:
    """
    Clean up directories older than specified days.
    
    Args:
        base_dir: Base directory to scan
        days_old: Age threshold in days
        
    Returns:
        Tuple of (cleaned_directories, failed_directories)
    """
    from datetime import datetime, timedelta
    import shutil
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    cutoff_timestamp = cutoff_time.timestamp()

    cleaned_dirs = []
    failed_dirs = []

    for task_dir in base_dir.iterdir():
        if task_dir.is_dir() and task_dir.name.startswith("task_"):
            try:
                # Check if directory is old enough
                dir_mtime = task_dir.stat().st_mtime
                if dir_mtime < cutoff_timestamp:
                    # Remove the entire task directory
                    shutil.rmtree(task_dir)
                    cleaned_dirs.append(str(task_dir))
                    logger.info(f"Cleaned up old task directory: {task_dir}")
            except Exception as e:
                failed_dirs.append((str(task_dir), str(e)))
                logger.error(f"Failed to clean up {task_dir}: {e}")

    return cleaned_dirs, failed_dirs


# LightRAG utility functions
async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    return await openai_complete_if_cache(
        model="gpt-4o-mini",
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        **kwargs
    )


async def initialize_lightrag() -> LightRAG:
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=llm_model_func,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag
