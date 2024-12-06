import random
import string
import unicodedata
from typing import List, Optional, TypedDict

import httpx
from loguru import logger as log

# Base headers for httpx client
BASE_HEADERS = {
    "Referer": "https://www.tripadvisor.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}


class LocationData(TypedDict):
    """result dataclass for tripadvisor location data"""

    localizedName: str
    url: str
    HOTELS_URL: str
    ATTRACTIONS_URL: str
    RESTAURANTS_URL: str
    placeType: str
    latitude: float
    longitude: float


class Preview(TypedDict):
    url: str
    name: str


def normalize_text(text):
    return unicodedata.normalize("NFKC", text) if text else ""


def generate_request_id(length: int = 180) -> str:
    """Generate a random request ID for scraper."""
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(length)
    )


def get_http_client(follow_redirects: bool = True) -> httpx.AsyncClient:
    """Set up and return an HTTPX client with headers."""

    return httpx.AsyncClient(
        http2=True,
        default_encoding="utf-8",
        follow_redirects=follow_redirects,
        headers=BASE_HEADERS,
        timeout=httpx.Timeout(150.0),
        limits=httpx.Limits(max_connections=5),
    )
