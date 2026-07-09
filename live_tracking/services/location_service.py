import requests

from django.conf import settings
from django.utils import timezone

from live_tracking.models import (
    LiveLocation,
    ApiLog,
)

from .auth_service import TrackingAuthService
class LocationService:

    @classmethod
    def fetch_location(cls, session):

        token = TrackingAuthService.get_tracking_token()

        if not token["success"]:
            return token

        url = (
            f"{settings.TELENITY_LOCATION_API}/"
            f"msisdnList/{session.driver_mobile}"
            f"?lastResult=True"
        )

        headers = {
            "Token": token["token"],
            "Content-Type": "application/json"
        }

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )

            ApiLog.objects.create(
                api_name="Location API",
                request_data={"mobile": session.driver_mobile},
                response_data=response.text,
                status_code=response.status_code
            )

            if response.status_code != 200:

                return {
                    "success": False,
                    "message": response.text
                }

            data = response.json()

            terminal = data["terminalLocation"][0]

            current = terminal["currentLocation"]

            session.last_latitude = current["latitude"]
            session.last_longitude = current["longitude"]

            session.last_location = current.get(
                "detailedAddress",
                ""
            )

            session.last_updated = timezone.now()

            session.status = "active"

            session.save()

            LiveLocation.objects.create(

                session=session,

                latitude=current["latitude"],

                longitude=current["longitude"],

                location_name=current.get(
                    "detailedAddress",
                    ""
                ),

                accuracy=0,

                received_at=timezone.now()

            )

            return {

                "success": True,

                "location": current

            }

        except Exception as e:

            return {

                "success": False,

                "message": str(e)

            }
