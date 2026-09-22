import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

async def test_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            "/api/auth/me",
            "/api/dashboard/summary",
            "/api/collection/transactions",
            "/api/recon/results",
            "/api/recon/stats",
            "/api/exceptions",
            "/api/sla/claims",
            "/api/refunds/cases",
            "/api/devolution/claims",
            "/api/accounting/vouchers",
            "/api/accounting/suspense",
            "/api/masters/banks",
            "/api/masters/sources",
            "/api/upload/batches",
        ]
        
        print("Testing Backend API Endpoints with Seeded Data:")
        for ep in endpoints:
            try:
                res = await client.get(ep)
                print(f"  [{res.status_code}] {ep} -> {len(res.content)} bytes")
            except Exception as e:
                print(f"  [ERR] {ep}: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
