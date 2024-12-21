import argparse


class TripAdvisorParser:
    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(description="TripAdvisor Data Fetcher")
        parser.add_argument(
            "--project_id",
            default="tripadvisor-recommendations",
            help="Project ID for TripAdvisor",
        )
        parser.add_argument(
            "--geo_dataset_id", default="dm_tripadvisor_models", help="Geo dataset ID"
        )
        parser.add_argument(
            "--geo_table_id",
            default="base_tripadvisor__geolocation",
            help="Geo table ID",
        )
        parser.add_argument(
            "--credentials_path", default="sa.json", help="Path to the credentials file"
        )
        parser.add_argument(
            "--api_key_env_var",
            default="TRIPADVISOR_API_KEY",
            help="Environment variable for API key",
        )
        parser.add_argument(
            "--rapid_api_key_env",
            default="RAPID_API_KEY",
            help="Environment variable for Rapid API key",
        )
        parser.add_argument(
            "--dataset_id", default="raw_tripadvisor", help="Raw dataset ID"
        )
        parser.add_argument(
            "--location_list_table_id",
            default="source_tripadvisor__api_info_v2",
            help="Location list table ID",
        )
        parser.add_argument(
            "--scraper_table_id",
            default="source_tripadvisor__scrape_info",
            help="Scraper table ID",
        )
        parser.add_argument(
            "--max_locations",
            type=int,
            default=-1,
            help="Maximum locations to fetch",
        )
        parser.add_argument(
            "--api",
            action="store_true",
            default=False,
            help="Run the API fetcher",
        )
        parser.add_argument(
            "--scrape",
            action="store_true",
            default=False,
            help="Run the scraper",
        )
        parser.add_argument(
            "--backfill",
            action="store_true",
            default=False,
            help="Run the backfiller",
        )

        return parser.parse_args()
