import os
import asyncio
import time
import unicodedata
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from univy.constants import UPLOAD_DIR, OUTPUT_DIR
from univy.lightrag_utils import initialize_lightrag


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


async def ingest_texts_to_lightrag(texts: list[str], source_files: list[str]) -> None:
    """
    Ingest texts to LightRAG.
    """
    rag = None
    try:
        rag = await initialize_lightrag()
        await rag.apipeline_enqueue_documents(
            input=texts,
            file_paths=source_files
        )
        await rag.apipeline_process_enqueue_documents()
        logger.info(
            f"Successfully ingested {len(source_files)} files into LightRAG")
    except Exception as e:
        logger.error(f"Error ingesting to LightRAG: {e}")
        raise
    finally:
        if rag:
            await rag.finalize_storages()


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
