import requests
from django.conf import settings

import random

class TelenityService:

    def send_tracking_sms(self, mobile):

        return {
            "success": True,
            "tracking_reference": f"TRK{mobile[-6:]}",
            "message": "Tracking SMS sent successfully."
        }


    def get_location(self, tracking_reference):

        locations = [

            {
                "location": "Chennai",
                "latitude": 13.0827,
                "longitude": 80.2707
            },

            {
                "location": "Sriperumbudur",
                "latitude": 12.9675,
                "longitude": 79.9418
            },

            {
                "location": "Vellore",
                "latitude": 12.9165,
                "longitude": 79.1325
            },

            {
                "location": "Krishnagiri",
                "latitude": 12.5186,
                "longitude": 78.2137
            },

            {
                "location": "Salem",
                "latitude": 11.6643,
                "longitude": 78.1460
            },

            {
                "location": "Namakkal",
                "latitude": 11.2194,
                "longitude": 78.1674
            },

            {
                "location": "Karur",
                "latitude": 10.9601,
                "longitude": 78.0766
            },

            {
                "location": "Dindigul",
                "latitude": 10.3624,
                "longitude": 77.9695
            },

            {
                "location": "Madurai",
                "latitude": 9.9252,
                "longitude": 78.1198
            }

        ]

        location = random.choice(locations)

        return {

            "success": True,

            "tracking_reference": tracking_reference,

            "status": "active",

            "latitude": location["latitude"],

            "longitude": location["longitude"],

            "location": location["location"],

            "accuracy": random.randint(30, 150)

        }

class TelenityService1:

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