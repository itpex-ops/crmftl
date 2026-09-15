import requests

from django.conf import settings

from .auth_service import TrackingAuthService
from live_tracking.models import ApiLog


class ModifyService:

    @classmethod
    def start_tracking(cls, session):

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):
            return auth

        if not session.entity_id:
            return {
                "success": False,
                "message": "Entity ID is missing."
            }

        token = auth["token"]

        url = f"{settings.TELENITY_MODIFY_API}/{session.entity_id}"

        headers = {
            "Token": token,
            "Content-Type": "application/json"
        }

        payload = {
            "isActive": True,
            "isTracked": True
        }

        print("\n" + "=" * 80)
        print("MODIFY API REQUEST")
        print("=" * 80)
        print("URL :", url)
        print("Payload :", payload)

        try:

            response = requests.put(
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )

            try:
                response_data = response.json()
            except Exception:
                response_data = {
                    "raw_response": response.text
                }

            ApiLog.objects.create(
                api_name="Modify API",
                request_url=url,
                request_method="PUT",
                request_headers={"Token": "********"},
                request_body=payload,
                response_code=response.status_code,
                response_body=response_data,
            )

            print("=" * 80)
            print("MODIFY API RESPONSE")
            print("=" * 80)
            print("Status :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            if response.status_code == 200:
                session.tracking_enabled = True
                session.save()

                return {
                    "success": True,
                    "response": response_data
                }

            return {
                "success": False,
                "status_code": response.status_code,
                "message": response_data
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }