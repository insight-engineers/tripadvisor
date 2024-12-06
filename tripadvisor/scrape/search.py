import asyncio
import json
import math
from typing import List, Optional
from urllib.parse import urljoin

import httpx
from loguru import logger as log
import random
import string
from parsel import Selector
from tripadvisor.scrape.utils import LocationData, get_http_client


async def scrape_location_data(
    query: str, client: httpx.AsyncClient
) -> List[LocationData]:
    """
    scrape search location data from a given query.
    e.g. "New York" will return us TripAdvisor's location details for this query
    """
    log.info(f"Scraping location data: {query}")
    payload = [
        {
            "variables": {
                "request": {
                    "query": query,
                    "limit": 1,
                    "scope": "WORLDWIDE",
                    "locale": "en-US",
                    "scopeGeoId": 293925,  # Ho Chi Minh City
                    "searchCenter": None,
                    "types": [
                        "LOCATION",
                    ],
                    "locationTypes": [
                        "EATERY",
                    ],
                    "userId": None,
                    "context": {},
                    "enabledFeatures": ["articles"],
                    "includeRecent": True,
                }
            },
            # Every graphql query has a query ID that doesn't change often:
            "query": "84b17ed122fbdbd4",
            "extensions": {"preRegisteredQueryId": "84b17ed122fbdbd4"},
        }
    ]

    # we need to generate a random request ID for this request to succeed
    random_request_id = "".join(
        random.choice(string.ascii_lowercase + string.digits) for i in range(180)
    )
    headers = {
        "X-Requested-By": random_request_id,
        "Referer": "https://www.tripadvisor.com/Restaurants",
        "Origin": "https://www.tripadvisor.com",
    }
    result = await client.post(
        url="https://www.tripadvisor.com/data/graphql/ids",
        json=payload,
        headers=headers,
    )
    data = json.loads(result.content)
    results = data[0]["data"]["Typeahead_autocomplete"]["results"]
    results = [r["details"] for r in results]  # strip metadata
    log.info(f"found {len(results)} results")

    return results


# example use:
if __name__ == "__main__":
    client = get_http_client(follow_redirects=True)

    async def run():
        result = await scrape_location_data(
            "/Restaurant_Review-g293925-d14090638-Reviews-Cork_Bottle_Wine_Grill-Ho_Chi_Minh_City.html",
            client,
        )
        print(json.dumps(result, indent=2))

    asyncio.run(run())
