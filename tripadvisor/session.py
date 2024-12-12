import os
import requests
from requests_ip_rotator import ApiGateway
from bs4 import BeautifulSoup
from typing import Optional
from loguru import logger as log
import asyncio

from tripadvisor._constants import (
    SCRAPE_DELAY,
    BASE_HEADERS,
)


class RotatingSessionManager:
    def __init__(self, base_url, headers=BASE_HEADERS):
        """
        Initialize a rotating session manager for a given base URL.

        Args:
            base_url (str): Base URL to create the IP rotating gateway for.
            headers (dict, optional): Dictionary of default headers to use. Defaults to None.
        """
        if not (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_ACCESS_KEY_SECRET")):
            raise ValueError("AWS credentials must be set in .env file")

        # singapore and sydney because they are the only AP regions that speak english
        self.regions = ["ap-southeast-1", "ap-southeast-2"]

        self.base_url = base_url
        self.default_headers = {
            **headers,
            **{
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
        }
        self.gateway = None
        self.session = None

    def start(self):
        """
        Start the API gateway and create a session.

        Creates an ApiGateway and mounts it to a new requests Session.
        """
        log.info("Starting API gateway and session")
        self.gateway = ApiGateway(
            self.base_url,
            regions=["ap-southeast-1"],
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("AWS_ACCESS_KEY_SECRET"),
            verbose=False,
        )

        self.gateway.start()
        self.session = requests.Session()
        self.session.mount(self.base_url, self.gateway)

        if self.session and self.gateway:
            log.info("API gateway and session started successfully")

    def shutdown(self):
        """
        Shutdown the API gateway and clean up resources.

        Closes the gateway and invalidates the current session.
        """
        if self.gateway:
            self.gateway.shutdown()
            self.gateway = None

        if self.session:
            self.session.close()
            self.session = None

        log.success("API gateway and session shutdown successfully")

    async def fetch(self, url, method="get", headers=None, **kwargs):
        """
        Fetch a URL using the rotating session.

        Args:
            url (str): URL to fetch.
            method (str, optional): HTTP method. Defaults to 'get'.
            headers (dict, optional): Headers to override default headers. Defaults to None.
            **kwargs: Additional arguments to pass to requests method.

        Returns:
            requests.Response: Response object from the HTTP request.

        Raises:
            RuntimeError: If the session has not been started before fetching.
        """
        try:
            if not self.session:
                raise RuntimeError(
                    "Session must be started with start() method before fetching"
                )

            request_headers = {**self.default_headers, **(headers or {})}
            request_method = getattr(self.session, method.lower())
            return request_method(url, headers=request_headers, **kwargs)
        except Exception as e:
            log.error(f"Unexpected err fetching URL: {url} | Error: {e}")

    async def fetch_soup_from_url(
        self, url: str, method="get", headers=None, **kwargs
    ) -> Optional[BeautifulSoup]:
        """
        Fetch a URL and return the page source as a BeautifulSoup object.

        Parameters:
            url (str): The URL to fetch.
            method (str, optional): HTTP method. Defaults to 'get'.
            headers (dict, optional): Headers to override default headers. Defaults to None.
            **kwargs: Additional arguments to pass to requests

        Returns:
            Optional[BeautifulSoup]: The parsed page source, or None if the fetch fails.
        """

        try:
            response = await self.fetch(url, method, headers, **kwargs)
            print(response.text)

            assert response.status_code != 403, "Blocked by TripAdvisor"
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            log.error(f"Error fetching URL: {url} | Error: {e}")
        finally:
            await asyncio.sleep(SCRAPE_DELAY)
