import requests

from django.conf import settings

from .auth_service import TrackingAuthService

from live_tracking.models import ApiLog


class DeleteService:
    @classmethod
    def delete_tracking(cls, session):
        auth = TrackingAuthService.get_tracking_token()
        if not auth.get("success"):
            return auth
        token = auth["token"]
        mobile = str(session.driver_mobile).strip()
        if mobile.startswith("+91"):
            mobile = mobile.replace("+91", "")
        if not mobile.startswith("91"):
            mobile = "91" + mobile
        url = settings.TELENITY_DELETE_API
        headers = {
            "x-access-token": token,
            "Content-Type": "application/json"
        }
        payload = {
            "msisdnList": [
                mobile
            ]
        }
        print("\n")
        print("=" * 80)
        print("DELETE API REQUEST")
        print("=" * 80)
        print("URL :", url)
        print("Headers :", headers)
        print("Payload :", payload)
        print("=" * 80)
        try:
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )
            print("\n")
            print("=" * 80)
            print("DELETE API RESPONSE")
            print("=" * 80)
            print("Status :", response.status_code)
            print("Response :", response.text)
            print("=" * 80)
            try:
                response_data = response.json()
            except Exception:
                response_data = {
                    "raw_response": response.text
                }
            ApiLog.objects.create(
                api_name="Delete API",
                request_url=url,
                request_method="POST",
                request_headers={
                    "x-access-token": "********"
                },
                request_body=payload,
                response_code=response.status_code,
                response_body=response_data
            )
            if (
                response.status_code == 200 and
                response_data.get("success") is True
            ):
                session.status = "stopped"
                session.tracking_enabled = False
                session.consent_received = False
                session.latitude = None
                session.longitude = None
                session.last_location = None
                session.last_updated = None
                session.location_status = None
                session.entity_id = None
                session.consent_reference = None
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
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "Connection Timeout."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "Unable to connect to Telenity Server."
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
