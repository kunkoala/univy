import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger

setup_logger("lightrag", level="INFO")

WORKING_DIR = "./rag_storage"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_name="gpt-4.1-mini"
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag


async def main():
    rag = None
    try:
        # Initialize RAG instance
        rag = await initialize_rag()
        rag.insert("Your text")

        # Perform hybrid search
        mode = "hybrid"
        print(
            await rag.query(
                "What are the top themes in this story?",
                param=QueryParam(mode=mode)
            )
        )

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if rag:
            await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main())
