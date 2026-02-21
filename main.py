from dotenv import load_dotenv
import os
from provider.ebay import EbayAPI
from provider.temu import TemuAPI

if __name__ == "__main__":
    load_dotenv()
    ebay_api = EbayAPI(os.getenv("EBAY_APP_ID"))
    temu_api = TemuAPI()

    # Example usage
    ebay_results = ebay_api.search("laptop")
    temu_results = temu_api.search("laptop")

    print("eBay Results:", ebay_results)
    print("Temu Results:", temu_results)
