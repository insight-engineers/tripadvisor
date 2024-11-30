import requests
import dotenv
import os


class TripAdvisorAPI:
    BASE_URL = "https://api.content.tripadvisor.com/api/v1/location/nearby_search"

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is not set. Please provide a valid API key.")
        self.api_key = api_key

    def get_nearby_locations(self, lat, long):
        url = f"{self.BASE_URL}?latLong={lat},{long}&key={self.api_key}"
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()


if __name__ == "__main__":
    lat = 10.8231
    long = 106.6297
    dotenv.load_dotenv()
    api_key = os.getenv("TRIPADVISOR_API_KEY")

    try:
        api = TripAdvisorAPI(api_key)
        locations = api.get_nearby_locations(lat, long)
        print(locations)
    except Exception as e:
        print(f"An error occurred: {e}")
