import httpx
from univy.config import settings
from typing import Any, Dict


class LightRAGClient:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.LIGHTRAG_API_KEY
        self.base_url = (base_url or settings.LIGHTRAG_URL).rstrip("/")
        self.headers = {"X-API-KEY": self.api_key}

    def _handle_response(self, func):
        async def wrapper(*args, **kwargs):
            try:
                resp = await func(*args, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                return {"status": "error", "message": f"HTTP error: {e.response.text}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return wrapper

    async def post_text(self, text: str) -> Dict[str, Any]:
        """
        Send a POST request to /documents/text with the given text.
        Returns the InsertResponse (status, message) or an error dict.
        """
        url = f"{self.base_url}/documents/text"
        @self._handle_response
        async def do_post():
            async with httpx.AsyncClient() as client:
                return await client.post(url, headers=self.headers, json={"text": text})
        return await do_post()

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the current status of the document indexing pipeline from /documents/pipeline_status.
        Returns the JSON response or an error dict.
        """
        url = f"{self.base_url}/documents/pipeline_status"
        @self._handle_response
        async def do_get():
            async with httpx.AsyncClient() as client:
                return await client.get(url, headers=self.headers)
        return await do_get()

    # You can add more methods for other endpoints as needed
