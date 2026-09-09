import requests
from django.conf import settings
import random
class TelenityService:

    def send_tracking_sms(self, mobile):

        payload = {
            "mobile": mobile
        }

        response = requests.post(
            settings.TELENITY_SMS_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.TELENITY_API_KEY}"
            },
            timeout=30
        )

        return response.json()


    def get_location(self, tracking_reference):

        response = requests.get(
            settings.TELENITY_LOCATION_URL,
            params={
                "tracking_reference": tracking_reference
            },
            headers={
                "Authorization": f"Bearer {settings.TELENITY_API_KEY}"
            },
            timeout=30
        )

        return response.json()