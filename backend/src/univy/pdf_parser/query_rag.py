import os
import sys
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_embed, gpt_4o_mini_complete
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger
from pdfreader import PdfParserApp

setup_logger("lightrag", level="INFO")

WORKING_DIR = "./rag_storage"
if not os.path.exists(WORKING_DIR):
    raise RuntimeError(
        f"RAG storage directory '{WORKING_DIR}' does not exist. Run the ingestion script first.")


class CustomRAG:
    def __init__(self):
        self.rag = LightRAG(
            working_dir=WORKING_DIR,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        self.markdown_content = ""

    async def initialize_rag(self):
        await self.rag.initialize_storages()
        await initialize_pipeline_status()

    async def load_document(self, document_path):
        print("\n ===== RAG load document ====== \n")
        print(f"DOCUMENT PATH: {document_path}")
        print("\n ===================== \n")

        try:
            pdf_parser = PdfParserApp(document_path)
            pdf_parser.parse_pdf()
            markdown_content = pdf_parser.get_markdown()
            self.markdown_content = markdown_content
            print("\n ===== RAG load document ====== \n")
            print("DOCUMENT LOADED SUCCESSFULLY")
            print(f"DOCUMENT: {self.markdown_content}")
            print("\n ===================== \n")
        except Exception as e:
            print(f"Error loading document: {e}")
            raise e

    async def insert_document(self):
        print("\n ===== RAG insert document ====== \n")
        print("\n ===================== \n")
        await self.rag.ainsert(self.markdown_content)

    async def query_rag(self, question, mode="hybrid"):
        print("\n ===================== \n")
        print(f"QUERY MODE: {mode}")
        print(f"QUERY: {question}")
        print("\n ===================== \n")
        result = await self.rag.aquery(
            question,
            param=QueryParam(mode=mode)
        )
        return result


async def main():
    rag = CustomRAG()
    await rag.initialize_rag()
    await rag.load_document("test_papers/validation_study_telemonitor.pdf")
    await rag.insert_document()
    print("\nEnter your questions about the document (type 'exit' or press Enter to quit):\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() == 'exit' or question == '':
            print("Exiting.")
            break
        result = await rag.query_rag(question)
        print("\n--- Answer ---\n")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
