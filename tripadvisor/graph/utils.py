import random
import string

import httpx
from loguru import logger as log

# Base headers for httpx client
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Referer": "https://www.tripadvisor.com",
    "Accept-Language": "en-US,en;q=0.9",
}


def generate_request_id(length: int = 180) -> str:
    """Generate a random request ID for scraper."""
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(length)
    )


async def get_http_client() -> httpx.AsyncClient:
    """Set up and return an HTTPX client with headers."""
    return httpx.AsyncClient(
        http2=True,
        headers=BASE_HEADERS,
        timeout=httpx.Timeout(150.0),
        limits=httpx.Limits(max_connections=5),
    )
