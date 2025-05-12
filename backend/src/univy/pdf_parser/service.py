import os
import json
import asyncio
from pdfreader import PdfParserApp
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_embed, gpt_4o_mini_complete
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger

setup_logger("lightrag", level="INFO")

WORKING_DIR = "./rag_storage"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

def get_chunks_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Adjust the key as per your JSON structure
    return [item['text'] for item in data if 'text' in item]

async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

async def main(pdf_path, output_dir="output"):
    rag = None
    try:
        # Derive the expected chunked JSON path
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        chunked_json_path = os.path.join(output_dir, f"{base_name}_content_list.json")

        if os.path.exists(chunked_json_path):
            print(f"Found existing chunked JSON: {chunked_json_path}")
            chunks = get_chunks_from_json(chunked_json_path)
        else:
            print("Chunked JSON not found, parsing PDF...")
            pdf_reader = PdfParserApp(pdf_path, output_dir=output_dir)
            pdf_reader.parse_pdf()
            pdf_reader.save_all()
            # Now load the just-created JSON
            chunks = get_chunks_from_json(chunked_json_path)

        # Initialize LightRAG
        rag = await initialize_rag()
        await rag.ainsert(chunks)

        # Query example
        question = "What are the main skills listed in this resume?"
        result = await rag.query(
            question,
            param=QueryParam(mode="hybrid")
        )
        print(result)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if rag:
            await rag.finalize_storages()

if __name__ == "__main__":
    asyncio.run(main("test_papers/Resume_Azhar_En_07042025_SWE.pdf"))






