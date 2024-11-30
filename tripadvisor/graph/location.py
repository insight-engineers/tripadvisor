import json
from typing import List, TypedDict
from loguru import logger as log
import httpx
from tripadvisor.graph.utils import generate_request_id


class LocationData(TypedDict):
    localizedName: str
    url: str
    HOTELS_URL: str
    ATTRACTIONS_URL: str
    RESTAURANTS_URL: str
    placeType: str
    latitude: float
    longitude: float


async def scrape_location_data(
    query: str, client: httpx.AsyncClient
) -> List[LocationData]:
    """Scrape location data from TripAdvisor for a given query."""
    log.info(f"Scraping location data for query: {query}")
    payload = [
        {
            "variables": {
                "request": {
                    "query": query,
                    "limit": 10,
                    "scope": "WORLDWIDE",
                    "locale": "en-US",
                    "types": ["LOCATION"],
                    "locationTypes": ["EATERY"],
                    "enabledFeatures": ["articles"],
                }
            },
            "query": "84b17ed122fbdbd4",
            "extensions": {"preRegisteredQueryId": "84b17ed122fbdbd4"},
        }
    ]
    headers = {
        "X-Requested-By": generate_request_id(),
        "Referer": "https://www.tripadvisor.com/Restaurants",
        "Origin": "https://www.tripadvisor.com",
    }
    response = await client.post(
        "https://www.tripadvisor.com/data/graphql/ids", json=payload, headers=headers
    )
    data = response.json()
    results = [
        r["details"] for r in data[0]["data"]["Typeahead_autocomplete"]["results"]
    ]
    log.info(f"Found {len(results)} results for query: {query}")
    return results
