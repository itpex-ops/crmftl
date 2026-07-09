import requests

from django.conf import settings

from .auth_service import TrackingAuthService
from ..models import TrackingSession, ApiLog


class ImportService:

    @classmethod
    def import_driver(cls, vehicle):

        token = TrackingAuthService.get_tracking_token()

        if not token["success"]:
            return token

        headers = {
            "Token": token["token"],
            "Content-Type": "application/json"
        }

        payload = {

            "msisdn": vehicle.driver_number,

            "resourceName": vehicle.driver_number,

            "referenceId": vehicle.ftl_no

        }

        url = settings.TELENITY_IMPORT_API

        try:

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            ApiLog.objects.create(

                api_name="Import API",

                request_data=payload,

                response_data=response.text,

                status_code=response.status_code

            )

            if response.status_code == 200:

                session, created = TrackingSession.objects.get_or_create(

                    vehicle=vehicle,

                    defaults={

                        "driver_mobile": vehicle.driver_number,

                        "tracking_reference": vehicle.ftl_no,

                        "status": "pending"

                    }

                )

                return {

                    "success": True,

                    "session": session,

                    "response": response.json()

                }

            return {

                "success": False,

                "message": response.text

            }

        except Exception as e:

            return {

                "success": False,

                "message": str(e)

            }