import os
from datetime import datetime

import requests


class TripAdvisorRapidAPI:

    def __init__(self, api_key):
        self.base_url = "https://real-time-tripadvisor-scraper-api.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "real-time-tripadvisor-scraper-api.p.rapidapi.com",
        }

    def get_restaurant_reviews(self, restaurant_url):
        endpoint = "/tripadvisor_restaurants_reviews_v2"
        querystring = {"restaurant": restaurant_url}
        response = requests.get(
            self.base_url + endpoint, headers=self.headers, params=querystring
        )
        return response.json()

    def parse_reviews(self, reviews):
        return [
            {
                "title": review["title"],
                "text": review["text"],
                "rating": float(review["rating"]),
                "review_date": datetime.strptime(
                    review["creationDate"], "%Y-%m-%d"
                ).strftime("%B %d, %Y"),
                "review_type": review["tripInfo"]["tripType"],
            }
            for review in reviews
        ]

    def get_parsed_restaurant_reviews(self, restaurant_url):
        reviews = self.get_restaurant_reviews(restaurant_url)

        if "data" not in reviews:
            return []

        return self.parse_reviews(reviews["data"])


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    api_key = os.getenv("RAPID_API_KEY")
    restaurant_url = "https://www.tripadvisor.com/Restaurant_Review-g293925-d14028387-Reviews-Kyushu_Sakaba_Sho-Ho_Chi_Minh_City.html"
    api = TripAdvisorRapidAPI(api_key)
    reviews = api.get_parsed_restaurant_reviews(restaurant_url)
    print(reviews)
