import os
import base64
import httpx
import asyncio
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@dataclass
class EbayAPI:
    api_base_url: str = 'https://api.ebay.com'
    ebay_access_token: str = os.getenv('EBAY_OAUTH_TOKEN')
    client_id: str = os.getenv('EBAY_APP_ID')
    client_secret: str = os.getenv('EBAY_APP_SECRET')
    refresh_token: str = os.getenv('EBAY_REFRESH_TOKEN')
    proxy_url: str = os.getenv('PROXY_URL')

    # --- 1. AUTHENTICATION & SELF-HEALING ---

    def refresh_access_token(self):
        """Exchanges refresh_token for a new access_token and updates .env."""
        if not self.refresh_token:
            logger.error("❌ EBAY_REFRESH_TOKEN missing.")
            return None

        url = f"{self.api_base_url}/identity/v1/oauth2/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_creds = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_creds}"
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory"
        }

        with httpx.Client(proxy=self.proxy_url) as client:
            try:
                response = client.post(url, headers=headers, data=payload)
                if response.status_code == 200:
                    new_token = response.json().get("access_token")
                    self.ebay_access_token = new_token
                    self.update_env_file("EBAY_OAUTH_TOKEN", new_token)
                    logger.info("✅ Token refreshed and saved to .env.")
                    return new_token
                else:
                    logger.error(f"❌ Refresh failed: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"❌ Refresh request error: {e}")
                return None

    def update_env_file(self, key, value):
        """Persists the new token to the .env file."""
        env_path = '.env'
        if not os.path.exists(env_path): return
        with open(env_path, 'r') as f: lines = f.readlines()
        with open(env_path, 'w') as f:
            found = False
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                    found = True
                else: f.write(line)
            if not found: f.write(f"{key}={value}\n")

    # --- 2. INVENTORY OPERATIONS ---

    async def get_active_listings(self):
        """Fetches active inventory items from eBay."""
        endpoint = f"{self.api_base_url}/sell/inventory/v1/inventory_item?limit=50"
        
        async def fetch(token):
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            async with httpx.AsyncClient(proxy=self.proxy_url) as client:
                return await client.get(endpoint, headers=headers)

        response = await fetch(self.ebay_access_token)
        
        if response.status_code == 401: # Token expired
            new_token = self.refresh_access_token()
            if new_token:
                response = await fetch(new_token)

        if response.status_code == 200:
            data = response.json()
            return self._format_items(data.get("inventoryItems", []))
        else:
            logger.error(f"Inventory Fetch Error: {response.status_code}")
            return []

    def _format_items(self, raw_items):
        """Maps eBay JSON to TEMU-compatible internal format."""
        return [{
            "itemID": item.get("sku"),
            "title": item.get("product", {}).get("title"),
            "price": item.get("product", {}).get("pricingSummary", {}).get("price", {}).get("value"),
            "quantity": item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity", 0),
            "itemSpecifics": {k: v[0] for k, v in item.get("product", {}).get("aspects", {}).items() if v}
        } for item in raw_items]

    # --- 3. TEST DATA SEEDING (DUMMY PRODUCTS) ---

    async def seed_dummy_data(self):
        """Standardized seeding with error handling for eBay Core Service errors."""
        loc_key = "MOCK_WAREHOUSE_01"
        sku = "TEST-SYNC-ITEM-001"
        
        headers = {
            "Authorization": f"Bearer {self.ebay_access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US", # Use en-US for high compatibility
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(proxy=self.proxy_url) as client:
            # 1. Create Location (using POST)
            # If it already exists, eBay will return 400 or 409 - we can ignore that.
            loc_data = {
                "location": {
                    "address": {
                        "addressLine1": "123 Test Street",
                        "city": "San Jose",
                        "stateOrProvince": "CA",
                        "postalCode": "95125",
                        "countryCode": "US"
                    }
                },
                "locationInstructions": "Deliver to front desk.",
                "name": "Main Warehouse",
                "locationTypes": ["WAREHOUSE"]
            }
            await client.post(f"{self.api_base_url}/sell/inventory/v1/location/{loc_key}", json=loc_data, headers=headers)
            
            # 2. Create/Update Inventory Item
            # Note: We must include the 'condition' properly
            item_data = {
                "availability": {
                    "shipToLocationAvailability": {"quantity": 10}
                },
                "condition": "NEW",
                "product": {
                    "title": "Professional Sync Test Product",
                    "description": "A test product for the TEMU sync engine project.",
                    "aspects": {
                        "Brand": ["SyncMaster"],
                        "Type": ["Test Item"]
                    },
                    "imageUrls": ["https://picsum.photos/200/300"]
                }
            }
            
            # We use PUT because it's idempotent (creates if missing, updates if exists)
            res = await client.put(f"{self.api_base_url}/sell/inventory/v1/inventory_item/{sku}", json=item_data, headers=headers)
            
            if res.status_code in [200, 201, 204]:
                logger.info(f"✅ Success! SKU {sku} is ready.")
            else:
                logger.error(f"❌ Product Seed Failed: {res.status_code} - {res.text}")

# --- EXECUTION BLOCK ---

if __name__ == "__main__":
    async def run_setup():
        eapi = EbayAPI()
        # 1. Try to refresh first to ensure we have a valid session
        eapi.refresh_access_token()
        # 2. Seed a dummy item so the sync has something to find
        await eapi.seed_dummy_data()
        # 3. Final verification fetch
        items = await eapi.get_active_listings()
        print(f"\nFinal Test: Found {len(items)} items in inventory.")

    asyncio.run(run_setup())