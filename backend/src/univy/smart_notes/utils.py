from univy.lightrag_utils import initialize_lightrag
from lightrag import QueryParam


async def retrieve_material(doc_id: str) -> str:
    rag = await initialize_lightrag()

    param = QueryParam(
        mode='local',
        top_k=10,
        ids=[doc_id],
        response_type='Multiple Paragraphs',
        max_token_for_text_unit=256,
    )

    try:
        ctx = await rag.aquery("What is the main idea of the document?", param=param)
        return ctx
    except Exception as e:
        print(f"Error retrieving material: {e}")
        return None
    finally:
        await rag.finalize_storages()
