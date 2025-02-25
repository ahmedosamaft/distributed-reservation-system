import httpx
from fastapi import HTTPException

async def forward_request(method: str, url: str, headers: dict = None, json: dict = None):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, json=json)
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError as ce:
        raise HTTPException(status_code=503, detail=f"Service unreachable: {ce}") from ce
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Service request failed: {e}") from e