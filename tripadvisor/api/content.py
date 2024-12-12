import asyncio
import os

import requests
from loguru import logger as log

from tripadvisor._constants import BASE_HEADERS, SCRAPE_DELAY


class TripAdvisorContentAPI:
    BASE_URL = "https://api.content.tripadvisor.com/api/v1/location/nearby_search"
    HEADERS = BASE_HEADERS

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is not set. Please provide a valid API key.")
        self.api_key = api_key

    def get_nearby_locations(self, lat, long):
        url = f"{self.BASE_URL}?category=restaurants&radius=1&radiusUnit=km&latLong={lat},{long}&key={self.api_key}"
        response = requests.get(url, headers=self.HEADERS)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    async def get_location_url(self, location_id, full=False):
        """Get redirect URL of a location on TripAdvisor."""
        try:
            asyncio.sleep(SCRAPE_DELAY / 2)
            location_url = f"https://www.tripadvisor.com/{location_id}"

            if full:
                response = requests.get(
                    f"https://www.tripadvisor.com/{location_id}", headers=self.HEADERS
                )
                location_url = response.url

        except Exception as e:
            log.error(f"An error occurred: {e}")
            location_url = None
        finally:
            asyncio.sleep(SCRAPE_DELAY / 2)
            return location_url


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    TEST_LAT, TEST_LONG = 10.8231, 106.6297

    try:
        api = TripAdvisorContentAPI(api_key)
        locations = api.get_nearby_locations(TEST_LAT, TEST_LONG)
        print(locations)
    except Exception as e:
        print(f"An error occurred: {e}")
