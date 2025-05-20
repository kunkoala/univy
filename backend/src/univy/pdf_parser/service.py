import os
from .pdfreader import PdfParserApp
import tempfile
from univy.lightrag_client import LightRAGClient

async def process_pdf_upload(file_content: bytes, filename: str, lightrag_client: LightRAGClient) -> dict:
    """
    Save uploaded file content, parse with PdfParserApp (MinerU), extract markdown, and upload it as a single text to LightRAG via HTTP API.
    """
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    output_dir = tempfile.mkdtemp(prefix="minerU_")
    try:
        # Parse PDF with MinerU pipeline
        parser = PdfParserApp(tmp_path, output_dir=output_dir)
        parser.parse_pdf()
        # parser.save_all()  # Not needed for just markdown
        # Get markdown content
        markdown = parser.get_markdown()
        if not markdown or not isinstance(markdown, str):
            raise RuntimeError("No markdown content extracted from PDF.")
        # Upload markdown to LightRAG via injected LightRAGClient
        return await lightrag_client.post_text(markdown)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        os.remove(tmp_path)
        # Optionally clean up output_dir if needed
