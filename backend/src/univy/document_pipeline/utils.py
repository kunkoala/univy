import os
import asyncio
import time
import unicodedata
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from univy.constants import UPLOAD_DIR, OUTPUT_DIR
from univy.lightrag_utils import initialize_lightrag


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
            doc_converter = setup_docling_converter(
                do_ocr=True, use_gpu=use_gpu)
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
    logger.info(
        f"Markdown file created: {md_file} in {processing_time:.2f} seconds")

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
        raise FileNotFoundError(
            f"File {pdf_file_name} not found in {UPLOAD_DIR}")
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


def cleanup_all_directories(base_dir: Path) -> Tuple[list, list]:
    """
    Delete all files and directories in the given base_dir.

    Args:
        base_dir: Base directory to clean up

    Returns:
        Tuple of (deleted_paths, failed_paths)
    """
    import shutil

    deleted = []
    failed = []

    for item in base_dir.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            deleted.append(str(item))
        except Exception as e:
            failed.append((str(item), str(e)))
            logger.error(f"Failed to delete {item}: {e}")
    return deleted, failed
