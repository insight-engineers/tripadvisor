#!/usr/bin/env python
#!Encoding: utf-8

"""
SCRAPE CONFIG (in seconds) between each request to avoid being blocked by TripAdvisor.
!Not change to lower than 2 second
"""
SCRAPE_ENCODING = "utf-8"
SCRAPE_DELAY = float(2.5)
SCRAPE_TIMEOUT = float(150.0)
SCRAPE_MAX_REVIEWS = int(300)  #! Should be divisible by 15


"""
!Headers for scraping/api TripAdvisor with http2 requests. Change with caution cause it may lead to blockage.
"""
BASE_URL = "https://www.tripadvisor.com"
BASE_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
BASE_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
BASE_LANGUAGE = "en-US,en;q=0.9,vi;q=0.8"

BASE_HEADERS = {
    "Referer": BASE_URL,
    "User-Agent": BASE_AGENT,
    "Accept": BASE_ACCEPT,
    "Accept-Language": BASE_LANGUAGE,
}
