import os

import requests


class TripAdvisorAPI:
    BASE_URL = "https://api.content.tripadvisor.com/api/v1/location/nearby_search"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is not set. Please provide a valid API key.")
        self.api_key = api_key

    def get_nearby_locations(self, lat, long):
        url = f"{self.BASE_URL}?category=restaurants&radius=1&radiusUnit=km&latLong={lat},{long}&key={self.api_key}"
        response = requests.get(url, headers=self.HEADERS)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def get_location_url(self, location_id, full=False):
        """Get redirect URL of a location on TripAdvisor."""
        if full:
            response = requests.get(
                f"https://www.tripadvisor.com/{location_id}", headers=self.HEADERS
            )
            return response.url

        return f"https://www.tripadvisor.com/{location_id}"


if __name__ == "__main__":
    lat = 10.8231  # Test only, lat of Thao Dien, District 2, HCMC
    long = 106.6297  # Test only, lat of Thao Dien, District 2, HCMC
    import dotenv

    dotenv.load_dotenv()

    api_key = os.getenv("TRIPADVISOR_API_KEY")

    try:
        api = TripAdvisorAPI(api_key)
        locations = api.get_nearby_locations(lat, long)
        print(locations)
    except Exception as e:
        print(f"An error occurred: {e}")
