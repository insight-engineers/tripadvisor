import asyncio
import unicodedata
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger as log

from tripadvisor._constants import (BASE_HEADERS, SCRAPE_DELAY,
                                    SCRAPE_ENCODING, SCRAPE_TIMEOUT)


def get_httpx_client(
    follow_redirects: bool = True, http2_enabled: bool = True, max_connections: int = 5
) -> httpx.AsyncClient:
    """Set up and return an HTTPX client with headers

    Parameters:
        follow_redirects (bool): Whether to follow redirects.
        http2_enabled (bool): Whether to enable HTTP/2.
        max_connections (int): The maximum number of connections to allow.
    """

    return httpx.AsyncClient(
        http2=http2_enabled,
        default_encoding=SCRAPE_ENCODING,
        follow_redirects=follow_redirects,
        headers=BASE_HEADERS,
        timeout=httpx.Timeout(SCRAPE_TIMEOUT),
        limits=httpx.Limits(max_connections=max_connections),
    )


async def fetch_soup_from_url(
    client: httpx.AsyncClient, url: str
) -> Optional[BeautifulSoup]:
    """
    Fetch a URL and return the page source as a BeautifulSoup object.

    Parameters:
        client (httpx.AsyncClient): async client create with httpx
        url (str): The URL to fetch.

    Returns:
        Optional[BeautifulSoup]: The parsed page source, or None if the fetch fails.
    """

    try:
        response = await client.get(url)
        response.raise_for_status()
        response.encoding = "utf-8"
        return BeautifulSoup(response.text, "html.parser")
    except httpx.RequestError as req_err:
        log.error(f"Request err fetching URL: {url} | Details: {req_err}")
    except Exception as e:
        log.error(f"Unexpected err fetching URL: {url} | Error: {e}")
    finally:
        await asyncio.sleep(SCRAPE_DELAY / 2)


def normalize_text(text):
    """Normalize a string value.

    Parameters:
        text (str): The string to normalize.
    """
    return unicodedata.normalize("NFKC", text) if text else ""


def normalize_int(text: str) -> int:
    """Normalize an integer value from a string

    Parameters:
        text (str): The string to normalize.
    """
    return int(text.strip().replace(",", "").replace("#", "").replace(".", ""))


def normalize_float(text: str) -> float:
    """Normalize a float value from a string.

    Parameters:
        text (str): The string to normalize.
    """
    return float(text.strip().replace(",", "").replace("#", ""))
