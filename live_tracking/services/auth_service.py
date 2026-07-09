import requests

from django.conf import settings


class TrackingAuthService:

    @classmethod
    def get_tracking_token(cls):

        url = "https://smarttrail.telenity.com/trail-rest/login"

        headers = {
            "Token": settings.TELENITY_TRACKING_KEY.strip()
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print("Tracking Status :", response.status_code)
        print("Tracking Response :", response.text)

        return response