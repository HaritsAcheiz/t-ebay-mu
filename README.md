🚀 eBay to TEMU Inventory Sync Engine

An asynchronous Python-based integration service that synchronizes real-time inventory levels and product data from the eBay Sell API to a TEMU Marketplace connector.
🛠️ Technical Highlights

    OAuth 2.0 Lifecycle: Implemented a self-healing OAuth 2.0 handshake with automatic refresh token rotation and .env persistence.

    Asynchronous Orchestration: Utilized asyncio and httpx to process inventory updates concurrently, minimizing latency during high-volume syncs.

    Robust Data Seeding: Developed a specialized utility to programmatically register eBay merchant locations and inject mock inventory for environment-agnostic testing.

    Schema Mapping: Engineered a transformation layer to bridge disparate data models between eBay's RESTful Inventory API and TEMU's listing requirements.

🏗️ Architecture

The system is divided into three core layers:

    Providers: Specialized API clients for eBay (Production) and TEMU (Mock/Sandbox).

    Orchestrator: The main.py engine that manages the data flow and transformation.

    Persistence: Secure credential management via environment variable injection and programmatic .env updates.

🚦 Getting Started

    Prerequisites: uv or pip, and an eBay Developer Account.

    Configuration: Populate .env with your Application ID, Cert ID, and RuName.

    Seeding: Run uv run provider/ebay.py to prepare the test environment.

    Synchronize: Execute uv run main.py.