import json
import hashlib
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from loguru import logger
from datetime import datetime

from univy.constants import UPLOAD_DIR, OUTPUT_DIR
from univy.lightrag_utils import initialize_lightrag
from univy.document_pipeline.models import DocumentMetadata, Base

from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.document import ConversionResult

from docling_core.types.doc import ImageRefMode


def generate_custom_doc_id(conv_res: ConversionResult) -> str:
    # generate using hashlib
    name = f"{conv_res.input.file.stem}_{time.time()}"
    return hashlib.sha256(name.encode()).hexdigest()


async def save_document_metadata_to_db(
    user_id: int,
    doc_ids: List[str],
    file_paths: List[str],
    processing_results: Dict[str, Any],
    task_id: str,
    processing_time: float,
    ingest_time: float
) -> List[DocumentMetadata]:
    """
    Save document metadata to database after successful processing
    
    Args:
        user_id: ID of the user who uploaded the documents
        doc_ids: List of generated document IDs
        file_paths: List of original file paths
        processing_results: Processing statistics and results
        task_id: Celery task ID
        processing_time: Total processing time in seconds
        ingest_time: LightRAG ingestion time in seconds
    
    Returns:
        List of saved DocumentMetadata objects
    """
    documents = []
    
    for doc_id, file_path in zip(doc_ids, file_paths):
        file_path_obj = Path(file_path)
        
        # Get file size
        file_size = file_path_obj.stat().st_size if file_path_obj.exists() else None
        
        # Create document metadata object
        document = DocumentMetadata(
            doc_id=doc_id,
            user_id=user_id,
            original_filename=file_path_obj.name,
            file_path=str(file_path),
            title=file_path_obj.stem,  # Use filename without extension as title
            processing_status="completed",
            processing_task_id=task_id,
            processing_results=processing_results,
            file_size=file_size,
            processing_time=processing_time,
            ingest_time=ingest_time,
            processed_at=datetime.utcnow()
        )
        documents.append(document)
    
    # Save to database (you'll need to implement this based on your database setup)
    # This is a placeholder - you'll need to integrate with your actual database session
    try:
        # Example with SQLAlchemy session:
        # from univy.database import get_db_session
        # async with get_db_session() as session:
        #     session.add_all(documents)
        #     await session.commit()
        
        logger.info(f"Saved {len(documents)} document metadata records to database")
        return documents
        
    except Exception as e:
        logger.error(f"Failed to save document metadata to database: {e}")
        raise


def export_documents(
    conv_results: Iterable[ConversionResult],
    output_dir: Path,
    markdown_output: bool = True,
    doctags_output: bool = True,
    json_output: bool = True,
) -> Tuple[int, int, int, list[str], list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failure_count = 0
    partial_success_count = 0
    generated_files = []
    converted_texts_lightrag_input = []
    converted_file_paths: list[str] = []
    doc_ids = []

    for conv_res in conv_results:
        if conv_res.status == ConversionStatus.SUCCESS:
            success_count += 1
            doc_filename = conv_res.input.file.stem
            logger.info(f"Conversion success for {doc_filename}")

            if json_output:
                logger.info(f"Exporting {doc_filename}.json")
                conv_res.document.save_as_json(
                    output_dir / f"{doc_filename}.json",
                    image_mode=ImageRefMode.PLACEHOLDER,
                )
                # Export Docling document format to JSON:
                with (output_dir / f"{doc_filename}.json").open("w") as fp:
                    fp.write(json.dumps(
                        conv_res.document.export_to_dict()))
                generated_files.append(
                    str(output_dir / f"{doc_filename}.json"))

            if doctags_output:
                logger.info(f"Exporting {doc_filename}.doctags")
                conv_res.document.save_as_doctags(
                    output_dir / f"{doc_filename}.doctags"
                )

                # Export Docling document format to doctags:
                with (output_dir / f"{doc_filename}.doctags").open("w") as fp:
                    fp.write(conv_res.document.export_to_doctags())
                generated_files.append(
                    str(output_dir / f"{doc_filename}.doctags"))

            if markdown_output:
                logger.info(f"Exporting {doc_filename}.md")
                conv_res.document.save_as_markdown(
                    output_dir / f"{doc_filename}.md",
                    image_mode=ImageRefMode.PLACEHOLDER,
                )
                # Export Docling document format to markdown:
                with (output_dir / f"{doc_filename}.md").open("w") as fp:
                    fp.write(conv_res.document.export_to_markdown())
                generated_files.append(
                    str(output_dir / f"{doc_filename}.md"))

            # the doctags are used for lightrag input text
            converted_texts_lightrag_input.append(
                conv_res.document.export_to_doctags())
            converted_file_paths.append(str(conv_res.input.file))

            # generate a custom doc id for the document
            doc_ids.append(generate_custom_doc_id(conv_res))

        elif conv_res.status == ConversionStatus.PARTIAL_SUCCESS:
            logger.info(
                f"Document {conv_res.input.file} was partially converted with the following errors:"
            )
            for item in conv_res.errors:
                logger.info(f"\t{item.error_message}")
            partial_success_count += 1
        else:
            logger.info(
                f"Document {conv_res.input.file} failed to convert.")
            failure_count += 1

    logger.info(
        f"Processed {success_count + partial_success_count + failure_count} docs, "
        f"SUCCESS: {success_count}, "
        f"PARTIAL SUCCESS: {partial_success_count}, "
        f"FAILURE: {failure_count}"
        f"DOC_IDS: {doc_ids}"
    )
    return success_count, partial_success_count, failure_count, generated_files, converted_texts_lightrag_input, converted_file_paths, doc_ids


async def ingest_texts_to_lightrag(texts: list[str], source_files: list[str], doc_ids: list[str]) -> None:
    """
    Ingest texts to LightRAG.
    """
    rag = None
    try:
        rag = await initialize_lightrag()
        await rag.ainsert(input=texts, file_paths=source_files, ids=doc_ids)

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
