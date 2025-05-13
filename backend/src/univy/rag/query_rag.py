import os
import logging
import logging.config
import asyncio

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_embed, openai_complete_if_cache, gpt_4o_mini_complete
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import logger, set_verbose_debug
from lightrag.types import GPTKeywordExtractionFormat
from univy.pdf_parser.pdfreader import PdfParserApp
from univy.config import settings

os.environ["AGE_GRAPH_NAME"] = settings.AGE_GRAPH_NAME

os.environ["POSTGRES_USER"] = settings.POSTGRES_USERNAME
os.environ["POSTGRES_PASSWORD"] = settings.POSTGRES_PASSWORD
os.environ["POSTGRES_DATABASE"] = settings.POSTGRES_DB
os.environ["POSTGRES_HOST"] = settings.POSTGRES_HOST
os.environ["POSTGRES_PORT"] = str(settings.POSTGRES_PORT)


WORKING_DIR = "./univy_pg"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


def configure_logging():
    """Configure logging for the application"""

    # Reset any existing handlers to ensure clean configuration
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "lightrag"]:
        logger_instance = logging.getLogger(logger_name)
        logger_instance.handlers = []
        logger_instance.filters = []

    # Get log directory path from environment variable or use current directory
    log_dir = os.getenv("LOG_DIR", os.getcwd())
    log_file_path = os.path.abspath(os.path.join(log_dir, "lightrag_demo.log"))

    print(f"\nLightRAG demo log file: {log_file_path}\n")
    os.makedirs(os.path.dirname(log_dir), exist_ok=True)

    # Get log file max size and backup count from environment variables
    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", 10485760))  # Default 10MB
    log_backup_count = int(
        os.getenv("LOG_BACKUP_COUNT", 5))  # Default 5 backups

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(levelname)s: %(message)s",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "file": {
                    "formatter": "detailed",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file_path,
                    "maxBytes": log_max_bytes,
                    "backupCount": log_backup_count,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "lightrag": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )

    # Set the logger level to INFO
    logger.setLevel(logging.INFO)
    # Enable verbose debug if needed
    set_verbose_debug(os.getenv("VERBOSE_DEBUG", "false").lower() == "true")


if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


"""
    This function is used to complete the prompt using the newest GPT-4.1-mini model since lightrag does not support it yet.
"""


async def gpt_41_mini_complete(
    prompt,
    system_prompt=None,
    history_messages=None,
    keyword_extraction=False,
    **kwargs,
) -> str:
    if history_messages is None:
        history_messages = []
    keyword_extraction = kwargs.pop("keyword_extraction", None)
    if keyword_extraction:
        kwargs["response_format"] = GPTKeywordExtractionFormat
    return await openai_complete_if_cache(
        "gpt-4.1-mini",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        **kwargs,
    )


async def initialize_rag() -> LightRAG:
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_max_token_size=32768,
        enable_llm_cache_for_entity_extract=True,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
        kv_storage="PGKVStorage",
        doc_status_storage="PGDocStatusStorage",
        graph_storage="PGGraphStorage",
        vector_storage="PGVectorStorage",
        auto_manage_storages_states=False,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag


async def load_documents(pdf_path: str):
    pdf_reader = PdfParserApp(pdf_path)
    pdf_reader.parse_pdf()
    return pdf_reader.get_markdown()


async def insert_documents(rag: LightRAG, documents: list[str]):
    await rag.ainsert(documents)


async def main():
    rag = await initialize_rag()
    documents = await load_documents("test_papers/Resume_Azhar_En_07042025_SWE.pdf")
    await insert_documents(rag, documents)

    print("\nEnter your questions about the document (type 'exit' or press Enter to quit):\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() == 'exit' or question == '':
            print("Exiting.")
            break
        result = await rag.aquery(question, param=QueryParam(mode="hybrid"))
        print("\n--- Answer ---\n")
        print(result)   

if __name__ == "__main__":
    asyncio.run(main())
