from fastapi import FastAPI, Request, HTTPException, Header
import os
import helpers
import yaml
import ulid
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

API_PREFIX = os.getenv("API_PREFIX", "api/v1")
VERIFY_TOKEN_PATH = os.getenv("VERIFY_TOKEN_PATH", "verify-token")
AUTH_SERVICE_NAME = os.getenv("AUTH_SERVICE_NAME", "auth")
CONFIG_FILE = os.getenv("CONFIG_FILE", "config.yml")


def load_config():
    """Load service mappings from YAML file"""
    try:
        with open(CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)
        logger.info(f"Successfully loaded config from {CONFIG_FILE}")
        return config.get("services", {})
    except FileNotFoundError:
        logger.error(f"Config file {CONFIG_FILE} not found")
        raise
    except Exception as e:
        logger.error(f"Error loading config file: {str(e)}")
        raise


SERVICE_MAP = load_config()

AUTH_SERVICE_URL = SERVICE_MAP.get(AUTH_SERVICE_NAME)
if not AUTH_SERVICE_URL:
    logger.error("Auth service URL not found in config")
    raise RuntimeError("Missing auth service configuration")


@app.api_route("/{service}/{subpath:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(
    service: str,
    subpath: str,
    request: Request,
    authorization: str = Header(default=None),
):
    """Generic proxy handler that forwards requests to microservices"""
    logger.info(f"Incoming {request.method} request for {service}/{subpath}")

    base_url = SERVICE_MAP.get(service)
    if not base_url:
        logger.info(f"Service not found: {service}")
        raise HTTPException(status_code=404, detail="Service not found")

    full_url = f"{base_url}/{API_PREFIX}/{service}/{subpath}"
    logger.debug(f"Constructed forwarding URL: {full_url}")

    headers = dict(request.headers.items())
    headers["request-id"] = ulid.new().str

    if service != AUTH_SERVICE_NAME:
        verify_token_url = f"{AUTH_SERVICE_URL}/{API_PREFIX}/{AUTH_SERVICE_NAME}/{VERIFY_TOKEN_PATH}"
        logger.debug(f"Verifying token with auth service: {verify_token_url}")

        try:
            token_response = await helpers.forward_request(
                "POST",
                verify_token_url,
                json={"token": authorization}
            )
            user_id = token_response.get("user_id")
            if user_id:
                logger.info(f"Successfully authenticated user: {user_id}")
                headers["user-id"] = str(user_id)
            else:
                logger.info("Token verification failed to return user_id")
                raise HTTPException(status_code=401, detail="Invalid token")
        except HTTPException as e:
            logger.info(f"Token verification failed: {e.detail}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.exception("Unexpected error during token verification")
            raise HTTPException(status_code=500, detail="Internal server error")

    try:
        body = await request.json() if await request.body() else None
        logger.debug(f"Request body content: {body}")
    except Exception as e:
        logger.info(f"Error parsing request body: {str(e)}")
        body = None

    try:
        logger.info(f"Forwarding request to {full_url}")
        response = await helpers.forward_request(
            request.method,
            full_url,
            headers=headers,
            json=body
        )
        logger.debug(f"Received response with status {response.status_code}")
        return response
    except HTTPException as e:
        logger.error(f"Service response error: {e.status_code} - {e.detail}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception("Failed to forward request")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting API gateway on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)