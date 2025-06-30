from lightrag import LightRAG
from lightrag.llm.openai import openai_embed, openai_complete_if_cache
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger
import os

from univy.config import settings


setup_logger("lightrag", level="INFO")

WORKING_DIR = "./rag_storage"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)
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
