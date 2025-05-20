import httpx
from univy.config import settings
from typing import Any, Dict

class LightRAGClient:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.LIGHTRAG_API_KEY
        self.base_url = (base_url or settings.LIGHTRAG_URL).rstrip("/")
        self.headers = {"X-API-KEY": self.api_key}

    async def post_text(self, text: str) -> Dict[str, Any]:
        """
        Send a POST request to /documents/text with the given text.
        Returns the InsertResponse (status, message) or an error dict.
        """
        url = f"{self.base_url}/documents/text"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=self.headers, json={"text": text})
                resp.raise_for_status()
                data = resp.json()
                # Ensure InsertResponse keys are present
                if "status" in data and "message" in data:
                    return data
                return {"status": "error", "message": "Unexpected response from LightRAG."}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "message": f"HTTP error: {e.response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the current status of the document indexing pipeline from /documents/pipeline_status.
        Returns the JSON response or an error dict.
        """
        url = f"{self.base_url}/documents/pipeline_status"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            return {"status": "error", "message": f"HTTP error: {e.response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # You can add more methods for other endpoints as needed 