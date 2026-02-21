# provider/temu.py
import os
import httpx
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class TemuAPI:
    # Pulls from .env -> Defaults to local mock server
    api_base_url: str = os.getenv("TEMU_API_BASE_URL", "http://127.0.0.1:8000")
    app_key: str = os.getenv("TEMU_APP_KEY")
    app_secret: str = os.getenv("TEMU_APP_SECRET")
    access_token: str = None

    async def get_access_token(self):
        """Asynchronously authenticates with the TEMU API."""
        endpoint = f"{self.api_base_url}/v1/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.app_key,
            "client_secret": self.app_secret
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                self.access_token = data.get("access_token")
                return self.access_token
        except httpx.HTTPError as e:
            logger.error(f"TEMU Auth failed: {e}")
            return None

    async def create_listing(self, payload):
        """Pushes a new product listing to TEMU."""
        endpoint = f"{self.api_base_url}/v1/goods/create"
        return await self._send_request("POST", endpoint, payload)

    async def update_listing(self, payload):
        """Updates price or inventory for an existing TEMU listing."""
        endpoint = f"{self.api_base_url}/v1/goods/update"
        return await self._send_request("POST", endpoint, payload)

    async def check_status(self, goods_id: int):
        """Queries the current status of a listing."""
        endpoint = f"{self.api_base_url}/v1/goods/status"
        params = {"goods_id": goods_id}
        return await self._send_request("GET", endpoint, params=params)

    async def _send_request(self, method, url, json_data=None, params=None):
        """Internal helper to handle authorized async requests."""
        if not self.access_token:
            await self.get_access_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, url, json=json_data, params=params, headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"TEMU API request failed: {e}")
            return {"success": False, "error": str(e)}