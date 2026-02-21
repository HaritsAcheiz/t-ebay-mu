from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="TEMU Dummy API")

@app.post("/v1/goods/create")
async def mock_temu_create(request: Request):
    data = await request.json()
    
    # Optional: Print to your console so you know the dummy received it
    print(f"--> [MOCK SERVER] Received payload for eBay Item: {data.get('external_goods_id')}")
    
    # Simulate TEMU's exact success response
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "goods_id": 987654321,
            "message": "Mock listing created successfully!"
        }
    )

@app.post("/v1/oauth/token")
async def mock_oauth_token():
    # Simulate the authentication endpoint
    return JSONResponse(
        status_code=200,
        content={
            "access_token": "dummy_token_abc123",
            "expires_in": 86400
        }
    )

@app.get("/v1/goods/status")
async def get_goods_status(goods_id: str):
    """
    Handles the verification check from the sync engine.
    """
    # This logic mimics a real database check
    valid_ids = ["987654321", "123456789"]
    
    if goods_id in valid_ids:
        return {
            "goods_id": goods_id,
            "status": "ACTIVE",
            "msg": "Success"
        }
    
    # If the ID isn't found, return a 404 (optional, but realistic)
    raise HTTPException(status_code=404, detail="Goods ID not found in TEMU mock database")