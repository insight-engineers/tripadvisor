import math
from typing import List, Optional, TypedDict
from urllib.parse import urljoin
from loguru import logger as log
from parsel import Selector
import httpx
from tripadvisor.graph.location import scrape_location_data

class Preview(TypedDict):
    url: str
    name: str

def parse_search_page(response: httpx.Response) -> List[Preview]:
    """Parse search page to extract preview details."""
    selector = Selector(response.text)
    previews = []
    for box in selector.css("div.listing_title>a"):
        previews.append({
            "url": urljoin(str(response.url), box.xpath("@href").get()),
            "name": box.xpath("text()").get("").strip(),
        })
    return previews

async def scrape_restaurants(query: str, client: httpx.AsyncClient, max_pages: Optional[int] = None) -> List[Preview]:
    """Scrape restaurant search results for a query."""
    location_data = await scrape_location_data(query, client)
    if not location_data:
        log.error(f"No location data found for query: {query}")
        return []

    restaurant_url = "https://www.tripadvisor.com" + location_data[0]["RESTAURANTS_URL"]
    response = await client.get(restaurant_url)
    response.raise_for_status()

    results = parse_search_page(response)
    if not results:
        log.error(f"No restaurants found for query: {query}")
        return []

    page_size = len(results)
    total_results = int(response.selector.xpath("//span/text()").re_first(r"(\d+)", "0"))
    total_pages = math.ceil(total_results / page_size)
    log.info(f"{query}: Total pages: {total_pages}, Total results: {total_results}")

    pages_to_scrape = min(max_pages or total_pages, total_pages)
    log.info(f"Scraping {pages_to_scrape} pages for query: {query}")
    return results
