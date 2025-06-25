import httpx
from typing import List, Optional

class APIClient:
    def __init__(self, base_url: str, timeout: float = 120.0, retries: int = 3):
        """
        Initialize the API client with the base URL.
        """
        self.base_url = base_url.rstrip("/")  # Ensure no trailing slash
        self.timeout = httpx.Timeout(timeout)  # Set the request timeout
        self.retries = retries
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        """
        A helper function to handle all types of API requests with proper error handling.
        """
        for attempt in range(1, self.retries + 1):
            try:
                response = await self.client.request(method, f"{self.base_url}{endpoint}", **kwargs)
                response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
                return response.json()
            except httpx.RequestError as e:
                print(f"Network error while making {method.upper()} request to {endpoint} (Attempt {attempt}/{self.retries}): {e}")
                if attempt == self.retries:
                    return {"error": f"Network error: {str(e)}"}
            except httpx.HTTPStatusError as e:
                print(f"HTTP error while making {method.upper()} request to {endpoint} (Attempt {attempt}/{self.retries}): {e}")
                if attempt == self.retries:
                    return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
            except Exception as e:
                print(f"Unexpected error (Attempt {attempt}/{self.retries}): {e}")
                if attempt == self.retries:
                    return {"error": f"Unexpected error: {str(e)}"}
        
    async def get_categories(self, text: str, categories: List[str], multi_label: bool):
        """
        Call the /categories endpoint.
        """
        return await self._make_request(
            method="POST",
            endpoint="/categories",
            json={"text": text, "categories": categories, "multi_label": multi_label},
        )

    async def get_embeddings(self, text: str):
        """
        Call the /embeddings/text endpoint.
        """
        return await self._make_request(
            method="POST",
            endpoint="/embeddings/text",
            json={"text": text},
        )

    async def get_emotions(self, text: str):
        """
        Call the /emotions endpoint.
        """
        return await self._make_request(
            method="POST",
            endpoint="/emotions",
            json={"text": text},
        )

    async def detect_sarcasm(self, text: str):
        """
        Call the /sarcasm endpoint.
        """
        return await self._make_request(
            method="POST",
            endpoint="/sarcasm",
            json={"text": text},
        )

    async def analyze_sentiment(self, text: str):
        """
        Call the /sentiment endpoint.
        """
        return await self._make_request(
            method="POST",
            endpoint="/sentiment",
            json={"text": text},
        )

    async def transcribe_audio(self, audio_path: str):
        """
        Call the /transcribe endpoint to transcribe speech from an audio file.

        Validates whether the file exists before proceeding.
        """
        try:
            # Open and send the audio file
            with open(audio_path, "rb") as file:
                files = {"file": file}
                return await self._make_request(
                    method="POST",
                    endpoint="/transcribe",
                    files=files,
                )
        except FileNotFoundError:
            print(f"Audio file not found: {audio_path}")
            return {"error": f"Audio file not found: {audio_path}"}
        except Exception as e:
            print(f"Error reading audio file {audio_path}: {e}")
            return {"error": f"Error reading audio file: {str(e)}"}

    async def analyze_topics(self, text: str, num_keywords: int = 6, topic_count: int = 3):
        """
        Call the /topics endpoint.
        """
        return await self._make_request(
            method="POST",
            endpoint="/topics",
            json={"text": text, "num_keywords": num_keywords, "topic_count": topic_count},
        )

    async def close(self):
        """
        Close the HTTP client to release resources.
        """
        await self.client.aclose()

