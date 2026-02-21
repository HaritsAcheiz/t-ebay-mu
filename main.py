import asyncio
import logging
from provider.ebay import EbayAPI
from provider.temu import TemuAPI

# Setup logging to see the magic happen
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def map_ebay_to_temu(ebay_item):
    """
    Translates the eBay dictionary into the format TEMU expects.
    This is the core 'Logic' of your project.
    """
    return {
        "external_goods_id": str(ebay_item.get("itemID")),
        "goods_name": ebay_item.get("title"),
        "skus": [{
            "external_sku_id": f"{ebay_item.get('itemID')}-DEFAULT",
            "inventory": ebay_item.get("quantity", 0),
            "price": ebay_item.get("price", 0.0),
            "variant_attributes": [
                {"name": k, "value": v} 
                for k, v in ebay_item.get("itemSpecifics", {}).items()
            ]
        }],
        "tax_code": "UK-Standard-20"
    }

async def sync_single_item(item, temu_client):
    """Handles the lifecycle for one item."""
    sku = item.get("itemID")
    logger.info(f"🔄 Processing SKU: {sku}")

    # 1. Transform
    payload = map_ebay_to_temu(item)

    # 2. Create on TEMU
    result = await temu_client.create_listing(payload)
    
    if result.get("success"):
        goods_id = result.get("goods_id")
        logger.info(f"✅ Synced {sku} -> TEMU Goods ID: {goods_id}")
        
        # 3. Double-check status (Verify it's 'PENDING' or 'ACTIVE')
        status = await temu_client.check_status(goods_id)
        logger.info(f"📊 TEMU Status for {goods_id}: {status.get('status')}")
    else:
        logger.error(f"❌ Failed to sync {sku}: {result.get('error')}")

async def run_orchestrator():
    logger.info("🚀 Starting eBay -> TEMU Sync Engine...")
    
    # Initialize both class-based clients
    ebay = EbayAPI()
    temu = TemuAPI()

    # 1. Pull data from eBay
    ebay_items = await ebay.get_active_listings()
    
    if not ebay_items:
        logger.warning("No items found on eBay to sync.")
        return

    # 2. Ensure TEMU is authenticated
    await temu.get_access_token()

    # 3. Sync all items concurrently using asyncio.gather
    tasks = [sync_single_item(item, temu) for item in ebay_items]
    await asyncio.gather(*tasks)
    
    logger.info("🏁 Sync process complete.")

if __name__ == "__main__":
    asyncio.run(run_orchestrator())