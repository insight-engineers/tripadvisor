import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from loguru import logger as log

from tripadvisor._constants import SCRAPE_DELAY
from tripadvisor.api.content import TripAdvisorContentAPI
from tripadvisor.api.rapid import TripAdvisorRapidAPI
from tripadvisor.bigquery import BigQueryHandler
from tripadvisor.parser import TripAdvisorParser
from tripadvisor.scrape.core import scrape_url


class TripAdvisorDataFetcher:
    def __init__(
        self,
        project_id: str,
        geo_dataset_id: str,
        geo_table_id: str,
        credentials_path: str,
        api_key_env_var: str,
        rapid_api_key_env: str,
    ):
        """
        Initialize the TripAdvisorDataFetcher.

        Args:
            project_id (str): GCP project ID.
            geo_dataset_id (str): BigQuery dataset ID.
            geo_table_id (str): BigQuery geolocation table ID.
            credentials_path (str): Path to service account JSON key file.
            api_key_env_var (str): env name for TripAdvisor API key.
            rapid_api_key_env (str): env name for RapidAPI key.
        """
        log.info("Initializing TripAdvisorDataFetcher...")

        if not project_id:
            raise ValueError("Please provide a GCP project ID")
        else:
            self.project_id = project_id

        self.bigquery = BigQueryHandler(self.project_id, credentials_path)
        self.geo_dataset_id = geo_dataset_id
        self.geo_table_id = geo_table_id
        self.api_key = os.getenv(api_key_env_var)
        self.rapid_api_key = os.getenv(rapid_api_key_env)

        if self.rapid_api_key:
            self.tripadvisor_rapid = TripAdvisorRapidAPI(self.rapid_api_key)

        if self.api_key:
            self.tripadvisor = TripAdvisorContentAPI(self.api_key)
        else:
            log.error(f"API key not found in env: {api_key_env_var}")
            raise ValueError(f"API key not found in env: {api_key_env_var}")

        log.success("TripAdvisorDataFetcher initialized successfully!")

    def fetch_geolocation(self) -> pd.DataFrame:
        """
        Fetch geolocation data from BigQuery.

        Returns:
            pd.DataFrame: DataFrame containing latitude and longitude data.
        """
        try:
            log.info("Fetching geolocation data from BigQuery...")
            query = f"""
            SELECT latitude, longitude
            FROM `{self.project_id}.{self.geo_dataset_id}.{self.geo_table_id}`
            """
            dataframe = self.bigquery.fetch_bigquery(query)
            log.success(f"Fetched {len(dataframe)} geolocation records from BigQuery.")
            return dataframe
        except Exception as e:
            log.error("Failed to fetch data from BigQuery.")
            log.exception(e)
            raise

    def fetch_location_data(self, lat, long) -> list:
        """
        Fetch location data from TripAdvisor API for a given latitude and longitude.

        Args:
            lat (float): Latitude.
            long (float): Longitude.

        Returns:
            list: List of location data dictionaries.
        """
        try:
            log.info(f"Fetching location data for latitude={lat}, longitude={long}...")
            location_data = self.tripadvisor.get_nearby_locations(lat, long)
            log.debug(f"Found {len(location_data['data'])} nearby locations.")
            return location_data["data"]
        except Exception as e:
            log.error(
                f"Failed to fetch location data for latitude={lat}, longitude={long}."
            )
            log.exception(e)
            return []

    def fetch_location_list(self, dataset_id, table_id) -> list:
        """
        Fetch a list of locations from BigQuery.

        Args:
            dataset_id (str): BigQuery dataset ID containing location data.
            table_id (str): BigQuery table ID containing location data.

        Returns:
            list: List of unique location IDs.
        """
        try:
            log.info(f"Fetching location list from: {dataset_id}.{table_id}")
            query = f"""
            SELECT DISTINCT location_id
            FROM `{self.project_id}.{dataset_id}.{table_id}`
            """
            dataframe = self.bigquery.fetch_bigquery(query)
            location_list = dataframe["location_id"].tolist()

            log.success(f"Fetched {len(location_list)} unique location IDs.")
            return location_list
        except Exception as e:
            log.error("No location list found in BigQuery.")
            log.exception(e)
            return []

    async def scrape_location(self, location) -> dict:
        """
        Scrape detailed information for a given location.

        Args:
            location (dict): A dictionary containing location information.

        Returns:
            dict: Scraped information for the location.
        """
        try:
            location_id = location["location_id"]
            location_url = self.tripadvisor.get_location_url(location_id, full=True)
            log.info(f"Scraping reviews for location ID: {location_id}...")
            scrape_info = await scrape_url(location_url)

            if (
                scrape_info["review_count_scraped"] == 0
                and scrape_info["review_count"] > 0
            ):
                log.warning(
                    f"No reviews scraped for location ID: {location_id}. Falling back to RapidAPI..."
                )
                reviews = self.tripadvisor_rapid.get_parsed_restaurant_reviews(
                    location_url
                )
                scrape_info["reviews"] = reviews

            return {
                "location_id": location_id,
                "location_url": location_url,
                "address_from_url": scrape_info["address_from_url"],
                "google_maps_link": scrape_info["google_maps_link"],
                "lat": scrape_info["lat"],
                "long": scrape_info["long"],
                "price_range": scrape_info["price_range"],
                "cuisine": scrape_info["cuisine"],
                "ranking": scrape_info["ranking"],
                "rating": scrape_info["rating"],
                "review_count": scrape_info["review_count"],
                "review_count_scraped": scrape_info["review_count_scraped"],
                "reviews": scrape_info["reviews"],
            }
        except Exception as e:
            log.error(f"Error scraping location: {location}")
            log.exception(e)
            return {}

    async def scrape_location_by_id(self, location_id) -> dict:
        """
        Scrape detailed information for a given location by ID.

        Args:
            location_id (str): The location ID to scrape.

        Returns:
            dict: Scraped information for the location.
        """
        try:
            log.info(f"Scraping reviews for location ID: {location_id}...")
            location_url = await self.tripadvisor.get_location_url(
                location_id=location_id,
                full=True,
            )
            scrape_info = await scrape_url(location_url)

            if (
                scrape_info["review_count_scraped"] == 0
                and scrape_info["review_count"] > 1
            ):
                log.warning(
                    f"No reviews scraped for location ID: {location_id}. Falling back to RapidAPI..."
                )
                reviews = self.tripadvisor_rapid.get_parsed_restaurant_reviews(
                    location_url
                )
                scrape_info["reviews"] = reviews

            return {
                "location_id": location_id,
                "location_url": location_url,
                "address_from_url": scrape_info["address_from_url"],
                "google_maps_link": scrape_info["google_maps_link"],
                "lat": scrape_info["lat"],
                "long": scrape_info["long"],
                "tel": scrape_info["tel"],
                "open_hour": scrape_info["open_hour"],
                "price_range": scrape_info["price_range"],
                "cuisine": scrape_info["cuisine"],
                "ranking": scrape_info["ranking"],
                "rating": scrape_info["rating"],
                "review_count": scrape_info["review_count"],
                "review_count_scraped": scrape_info["review_count_scraped"],
                "reviews": scrape_info["reviews"],
            }
        except Exception as e:
            log.error(f"Error scraping location ID: {location_id}")
            log.exception(e)
            return {}

    async def fetch_full_workflow(self, geolocations, max_workers=4) -> pd.DataFrame:
        """
        Fetch and scrape data for multiple geolocations.

        Args:
            geolocations (list): List of geolocation tuples (latitude, longitude).
            max_workers (int): Number of concurrent threads for fetching.

        Returns:
            pd.DataFrame: DataFrame containing scraped information.
        """
        log.info(f"Fetching for {len(geolocations)} geolocations...")

        scrape_info = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            loop = asyncio.get_event_loop()
            location_results = await asyncio.gather(
                *[
                    loop.run_in_executor(executor, self.fetch_location_data, lat, long)
                    for lat, long in geolocations
                ]
            )

        for loc_data in location_results:
            for location in loc_data:
                scrape_result = await self.scrape_location(location)
                if scrape_result:
                    scrape_info.append(scrape_result)
                await asyncio.sleep(SCRAPE_DELAY)

        log.success(f"Successfully scraped {len(scrape_info)} locations.")
        return pd.DataFrame(scrape_info)

    async def fetch_scraper_and_write(
        self,
        dataset_id: str,
        location_list_table_id: str,
        scraper_table_id: str,
        max_locations: int,
    ):
        """
        Fetch location data, scrape it, and write to BigQuery.

        Args:
            dataset_id (str): BigQuery dataset ID containing two tables.
            location_list_table_id (str): BigQuery table ID containing location data.
            scraper_table_id (str): BigQuery table ID to write scraped data.
        """
        try:
            location_list = self.fetch_location_list(dataset_id, location_list_table_id)
            scrape_info = []

            if max_locations != -1:
                location_list = location_list[:max_locations]

            for location_id in location_list:
                scrape_result = await self.scrape_location_by_id(location_id)
                if scrape_result:
                    scrape_info.append(scrape_result)

                await asyncio.sleep(SCRAPE_DELAY)

            scrape_df = pd.DataFrame(scrape_info)
            parquet_file_path = f"data/tripadvisor__scrape_info_{datetime.now().strftime('%Y%m%d')}.parquet"

            if not os.path.exists("data"):
                os.makedirs("data")

            self.save_to_parquet(scrape_df, parquet_file_path)
            self.bigquery.upload_parquet_to_bq(
                file_path=parquet_file_path,
                full_table_id=f"{dataset_id}.{scraper_table_id}",
                write_disposition="WRITE_TRUNCATE",
            )

            log.success("Data fetched, scraped, and written to BigQuery.")

        except Exception as e:
            log.error("Failed to fetch and write data.")
            log.exception(e)

    def save_to_parquet(self, dataframe, parquet_file_path):
        """
        Save a DataFrame to a Parquet file.

        Args:
            dataframe (pd.DataFrame): The DataFrame to save.
            parquet_file_path (str): The path to the Parquet file.
        """
        try:
            dataframe.to_parquet(parquet_file_path)
            log.success(f"Data saved to {parquet_file_path}.")
            return parquet_file_path
        except Exception as e:
            log.error(f"Failed to save DataFrame to {parquet_file_path}.")
            log.exception(e)


async def run():
    log.info("Starting TripAdvisor data fetcher script...")
    try:
        tripadvisor = TripAdvisorDataFetcher(
            project_id=args.project_id,
            geo_dataset_id=args.geo_dataset_id,
            geo_table_id=args.geo_table_id,
            credentials_path=args.credentials_path,
            api_key_env_var=args.api_key_env_var,
            rapid_api_key_env=args.rapid_api_key_env,
        )

        await tripadvisor.fetch_scraper_and_write(
            dataset_id=args.dataset_id,
            location_list_table_id=args.location_list_table_id,
            scraper_table_id=args.scraper_table_id,
            max_locations=args.max_locations,
        )

        log.info("TripAdvisor data fetcher script completed successfully!")
    except Exception as e:
        log.error("Script encountered an error.")
        log.exception(e)


if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(dotenv_path)
    args = TripAdvisorParser.parse_arguments()
    asyncio.run(run())
