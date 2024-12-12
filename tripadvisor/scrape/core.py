import asyncio
import json
import re
from typing import Dict, List

from loguru import logger as log

from tripadvisor._constants import SCRAPE_DELAY, SCRAPE_MAX_REVIEWS
from tripadvisor.scrape.utils import (fetch_soup_from_url, get_httpx_client,
                                      normalize_float, normalize_int,
                                      normalize_text)


async def parse_reviews(url, count):
    """Parse the reviews of a restaurant and return the parsed information
    Args:
        url (str): The URL of the restaurant.
        count (int): The number of all reviews in that page for cross-checking.
    """
    if count <= 0:
        log.warning("There are no reviews to parse. Skipping...")
        return []

    if not url.endswith("#REVIEWS"):
        url += "#REVIEWS"

    max_reviews = min(count, SCRAPE_MAX_REVIEWS)
    reviews = []
    page_increment = 15

    for start in range(0, max_reviews, page_increment):
        if start > 0:
            review_page_url = url.replace("-Reviews-", f"-Reviews-or{start}-")
        else:
            review_page_url = url
        log.info(f"Parsing: {review_page_url}")

        async with get_httpx_client(follow_redirects=False) as client:
            soup = await fetch_soup_from_url(client=client, url=review_page_url)

        review_blocks = soup.select("div[data-automation='reviewCard']")

        if not review_blocks:
            log.warning("No reviewCard found. Skipping...")
            break

        for review in review_blocks:
            try:
                review_tag = review.select_one("a[target*='_self']")
                review_userid = normalize_text(review_tag.get("href").split("/")[-1])
            except:
                review_userid = None

            try:
                review_title = normalize_text(
                    review.select_one(
                        "div[data-test-target='review-title'] a"
                    ).get_text(strip=True)
                )
            except:
                review_title = None

            try:
                review_text = normalize_text(
                    " ".join(
                        span.get_text(strip=True)
                        for span in review.select(
                            "div[data-test-target='review-body'] span"
                        )
                    )
                )
            except:
                review_text = None

            try:
                rating_element = review.select_one("div[class*='OSBmi'] svg title")
                rating = (
                    normalize_float(rating_element.get_text(strip=True).split(" ")[0])
                    if rating_element
                    else -1
                )
            except:
                rating = -1

            try:
                review_date = (
                    review.select_one(
                        "div[class*='neAPm'] div[class*='biGQs _P pZUbB ncFvv osNWb']"
                    )
                    .get_text()
                    .split(" ")[1:-1]
                )
                review_date = normalize_text(" ".join(review_date))
            except:
                review_date = None

            try:
                review_type = normalize_text(
                    review.select_one("div[class*='aVuQn'] span[class*='DlAxN']")
                    .get_text(strip=True)
                    .upper()
                )
            except:
                review_type = None

            reviews.append(
                {
                    "user": review_userid,
                    "title": review_title,
                    "text": review_text.replace("Read more", "").strip(),
                    "rating": rating,
                    "review_date": review_date,
                    "review_type": review_type,
                }
            )

        if len(reviews) >= max_reviews:
            break

        await asyncio.sleep(SCRAPE_DELAY)

    return reviews


async def parse_source_page(url, soup) -> Dict:
    """Parse the source page and return the parsed information

    Args:
        url (str): The URL of the source page.
        soup (BeautifulSoup): The BeautifulSoup object of the source
    """

    info_div = soup.find("div", {"data-test-target": "restaurant-detail-info"})

    try:
        tag_div = info_div.select_one("div[class*='CsAqy']")
        cuisine = tag_div.get_text().split("$")[-1].split(", ")[1:]
        log.info(f"Cuisine: {cuisine}")
    except:
        cuisine = []

    try:
        price_range = re.search(r"(\$+[-\s]*\$*)", tag_div.get_text())
        if price_range:
            price_range = price_range.group(0).strip()
            log.info(f"Price range: {price_range}")
        else:
            price_range = None
    except:
        price_range = None

    try:
        review_count = normalize_int(
            soup.select_one("span[data-automation='reviewCount']")
            .get_text()
            .split(" ")[0]
        )
        log.info(f"Review count: {review_count}")
    except:
        review_count = 0

    try:
        overview_tabs = soup.find_all(
            "div", {"data-automation": "OVERVIEW_TAB_ELEMENT"}
        )
        rating_tab = overview_tabs[0]
        location_tab = overview_tabs[-1]
    except:
        rating_tab = None
        location_tab = None

    try:
        rating_number = normalize_float(
            rating_tab.select_one("span[class*='biGQs _P fiohW uuBRH']").get_text(
                strip=True
            )
        )
    except:
        rating_number = None

    try:
        ranking = normalize_int(
            rating_tab.select_one("div[class*='biGQs _P pZUbB hmDzD'] b").get_text(
                strip=True
            )
        )
    except:
        ranking = None

    try:
        google_maps_link = location_tab.select_one("a").get("href")
    except:
        google_maps_link = None

    try:
        address_from_url = google_maps_link.split("@")[0].split("=")[-1]
    except:
        address_from_url = None

    try:
        lat, long = google_maps_link.split("@")[1].split(",")
    except:
        lat, long = None, None

    try:
        tel = location_tab.select_one("a[aria-label='Call']").get_text(strip=True)
    except:
        tel = None

    try:
        open_hour = info_div.select_one(
            "span[data-automation='top-info-hours']"
        ).get_text(strip=False)
    except:
        open_hour = None

    reviews = await parse_reviews(url, review_count)

    return {
        "url": url,
        "tel": tel,
        "open_hour": open_hour,
        "address_from_url": address_from_url,
        "google_maps_link": google_maps_link,
        "lat": float(lat.strip().replace(",", "")),
        "long": float(long.strip().replace(",", "")),
        "price_range": price_range,
        "cuisine": cuisine,
        "ranking": ranking,
        "rating": rating_number,
        "review_count": review_count,
        "review_count_scraped": len(reviews),
        "reviews": reviews,
    }


async def scrape_url(url: str) -> List[Dict]:
    """Scrape a URL and return the parsed information from the url.

    Args:
        url (str): The URL to scrape.
    """

    attempt, retries = 0, 100
    while attempt < retries:
        try:
            log.info(f"Fetching URL: {url} for attempt {attempt + 1}/{retries}...")

            async with get_httpx_client(follow_redirects=True) as client:
                soup = await fetch_soup_from_url(client=client, url=url)

            if (
                soup.find("div", {"data-automation": "reviewsOverviewSections"})
                is not None
                and soup.find("div", {"data-test-target": "restaurant-detail-info"})
                is not None
            ):
                parsed_info = await parse_source_page(url, soup)
                return parsed_info

            log.info("Retrying fetch for overview tab...")
            attempt += 1

        except Exception as e:
            log.info(f"Error on attempt {attempt + 1}/{retries}: {e}")
            log.info(f"Retrying in {SCRAPE_DELAY * 2} seconds...")
            attempt += 1
        except AssertionError:
            raise AssertionError("Get blocked by TripAdvisor. Not trying again.")
        finally:
            await asyncio.sleep(SCRAPE_DELAY * 2)


if __name__ == "__main__":
    TEST_URLS = [
        "https://www.tripadvisor.com/Restaurant_Review-g293925-d8614066-Reviews-Quan_B_i-Ho_Chi_Minh_City.html",
    ]

    async def run():
        for URL in TEST_URLS:
            parsed_info = await scrape_url(URL)
            sink_file_path = f"data/TEST_{URL.split('Reviews-')[1].split('-')[0]}.json"
            with open(sink_file_path, "w") as f:
                json.dump(parsed_info, f, indent=4)

    asyncio.run(run())
