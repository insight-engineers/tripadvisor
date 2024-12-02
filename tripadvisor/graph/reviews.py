import asyncio
import json
from typing import Dict, List, Optional

from httpx import AsyncClient
from parsel import Selector

client = AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    },
    follow_redirects=True,
)


def parse_reviews_page(result: str) -> List[Dict]:
    """Parse reviews from the TripAdvisor restaurant page"""
    selector = Selector(text=result)
    reviews = []

    # Loop through each review block
    review_blocks = selector.css("div[data-automation='reviewCard']")

    for review in review_blocks:
        title = review.css("div[data-test-target='review-title'] a::text").get()
        text = review.css("div[data-test-target='review-body'] span::text").get()
        rating_element = review.css("div[class*='OSBmi'] svg title::text").get()

        # review date
        review_date = review.css("div[class*='aVuQn']::text").get()
        reviews.append(
            {
                "title": title.strip() if title else "",
                "text": text.strip() if text else "",
                "rating": (
                    rating_element.strip().split(" ")[0] if rating_element else ""
                ),
                "review_date": review_date if review_date else "",
            }
        )

    return reviews


async def scrape_reviews(url: str) -> List[Dict]:
    """Scrape all reviews for a restaurant from the TripAdvisor page"""
    response = await client.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve the page: {response.status_code}")

    # Parse the reviews from the page source
    reviews = parse_reviews_page(response.text)
    return reviews


# Run the scraping
if __name__ == "__main__":

    async def run():
        # url = "https://www.tripadvisor.com/Restaurant_Review-g293925-d1717810-Reviews-Cuc_Gach_Quan-Ho_Chi_Minh_City.html"
        url = "https://www.tripadvisor.com/1717810"
        reviews = await scrape_reviews(url)
        print(json.dumps(reviews, indent=2))

    asyncio.run(run())
