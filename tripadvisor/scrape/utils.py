import unicodedata

import httpx


def get_http_client(follow_redirects: bool = True) -> httpx.AsyncClient:
    """Set up and return an HTTPX client with headers."""

    # Base headers for httpx client
    BASE_HEADERS = {
        "Referer": "https://www.tripadvisor.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    }

    return httpx.AsyncClient(
        http2=True,
        default_encoding="utf-8",
        follow_redirects=follow_redirects,
        headers=BASE_HEADERS,
        timeout=httpx.Timeout(150.0),
        limits=httpx.Limits(max_connections=5),
    )


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
