from fastapi import FastAPI, Request, HTTPException, Header
import os
import helpers
import yaml
import ulid
import uvicorn


app = FastAPI(port=5000)

API_PREFIX = os.getenv("API_PREFIX", "api/v1")
VERIFY_TOKEN_PATH = os.getenv("VERIFY_TOKEN_PATH", "verify-token")
AUTH_SERVICE_NAME = os.getenv("AUTH_SERVICE_NAME", "auth")
CONFIG_FILE = os.getenv("CONFIG_FILE", "config.yml")


def load_config():
    """Load service mappings from YAML file"""
    with open(CONFIG_FILE, "r") as file:
        config = yaml.safe_load(file)
    return config.get("services", {})


SERVICE_MAP = load_config()

# api.home/auth -> http://localhost:5001/{API_PREFIX}/{service}/{subpath:path} =  http://localhost:5001/api/v1/auth/login


@app.api_route("/{service}/{subpath:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(
    service: str,
    subpath: str,
    request: Request,
    authorization: str = Header(default=None),
):
    """Generic proxy handler that forwards requests to microservices with the same subpath"""
    base_url = SERVICE_MAP.get(service)
    if not base_url:
        raise HTTPException(status_code=404, detail="Service not found")

    full_url = f"{base_url}/{API_PREFIX}/{service}/{subpath}"
    headers = dict(request.headers.items())
    headers["request-id"] = ulid.new().str
    if service != AUTH_SERVICE_NAME:
        verify_token_url = (
            f"{AUTH_SERVICE_URL}/{API_PREFIX}/{AUTH_SERVICE_NAME}/{VERIFY_TOKEN_PATH}"
        )
        data = await helpers.forward_request(
            "POST", verify_token_url, json={"token": authorization}
        )
        user_id = data.get("user_id")
        headers["user-id"] = str(user_id)
        
    body = await request.json() if await request.body() else None
    return await helpers.forward_request(
        request.method, full_url, headers=headers, json=body
    )




if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=8000)
