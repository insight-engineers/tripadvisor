import asyncio
import json
from tripadvisor.graph.utils import get_http_client
from tripadvisor.graph.search import scrape_restaurants

async def main():
    client = await get_http_client()
    try:
        query = "Ho_Chi_Minh_City"
        results = await scrape_restaurants(query, client, 10)
        with open("restaurants.json", "w") as f:
            json.dump(results, f, indent=4)
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
