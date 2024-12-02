import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from loguru import logger as log

from tripadvisor.api.content import TripAdvisorAPI
from tripadvisor.graph.reviews import scrape_reviews


class TripAdvisorDataFetcher:
    def __init__(
        self, project_id, dataset_id, table_id, credentials_path, api_key_env_var
    ):
        log.info("Initializing TripAdvisorDataFetcher...")
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        self.client = bigquery.Client(project=project_id, credentials=self.credentials)
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.api_key = os.getenv(api_key_env_var)

        if not self.api_key:
            log.error(f"API key not found in environment variable: {api_key_env_var}")
            raise ValueError(
                f"API key not found in environment variable: {api_key_env_var}"
            )

        self.tripadvisor = TripAdvisorAPI(self.api_key)
        log.success("TripAdvisorDataFetcher initialized successfully!")

    def fetch_bigquery(self):
        log.info("Fetching geolocation data from BigQuery...")
        query = f"""
        SELECT latitude, longitude
        FROM `{self.dataset_id}.{self.table_id}`
        """
        dataframe = self.client.query(query).to_dataframe()
        log.success(f"Fetched {len(dataframe)} geolocation records from BigQuery.")
        return dataframe

    def fetch_location_data(self, lat, long):
        log.info(f"Fetching location data for latitude={lat}, longitude={long}...")
        location_data = self.tripadvisor.get_nearby_locations(lat, long)
        log.debug(f"Found {len(location_data['data'])} nearby locations.")
        return location_data["data"]

    async def scrape_location_reviews(self, location):
        location_id = location["location_id"]
        location_url = self.tripadvisor.get_location_url(location_id, full=True)
        log.info(f"Scraping reviews for location ID: {location_id}...")
        reviews = await scrape_reviews(location_url)
        log.debug(f"Scraped {len(reviews)} reviews for location ID {location_id}.")
        return {
            "location_id": location_id,
            "location_url": location_url,
            "reviews": reviews,
        }

    async def fetch_reviews(self, geolocations, max_workers=4):
        log.info(f"Fetching reviews for {len(geolocations)} geolocations...")

        location_info = []
        reviews = []

        # Fetch location data in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            loop = asyncio.get_event_loop()
            location_results = await asyncio.gather(
                *[
                    loop.run_in_executor(executor, self.fetch_location_data, lat, long)
                    for lat, long in geolocations
                ]
            )

        # Flatten the location data results
        for loc_data in location_results:
            location_info.extend(loc_data)

        # Scrape reviews asynchronously
        review_results = await asyncio.gather(
            *[self.scrape_location_reviews(location) for location in location_info]
        )

        # Collect review data
        reviews.extend(review_results)

        log.success(f"Successfully fetched reviews for {len(location_info)} locations.")
        return pd.DataFrame(reviews), pd.DataFrame(location_info)

    def save_to_parquet(self, dataframe, file_path):
        log.info(f"Saving DataFrame to {file_path}...")
        dataframe.to_parquet(file_path)
        log.success(f"Data saved to {file_path}.")


if __name__ == "__main__":

    async def run():
        log.info("Starting TripAdvisor data fetcher script...")
        fetcher = TripAdvisorDataFetcher(
            project_id="tripadvisor-recommendations",
            dataset_id="dm_tripadvisor",
            table_id="base_tripadvisor__geolocation",
            credentials_path="sa.json",
            api_key_env_var="TRIPADVISOR_API_KEY",
        )

        geolocations = fetcher.fetch_bigquery()[["latitude", "longitude"]].values
        log.info("Geolocation data prepared for review scraping.")

        reviews_df, location_info_df = await fetcher.fetch_reviews(geolocations)

        # Sink to parquet (in data folder)
        fetcher.save_to_parquet(reviews_df, "data/reviews.parquet")
        fetcher.save_to_parquet(location_info_df, "data/location_info.parquet")

        log.success("TripAdvisor data fetcher script completed successfully!")

    asyncio.run(run())
