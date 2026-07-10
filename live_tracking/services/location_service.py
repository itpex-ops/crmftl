import requests

from django.conf import settings

from .auth_service import TrackingAuthService
from live_tracking.models import ApiLog

from django.utils.dateparse import parse_datetime
from live_tracking.models import ApiLog, LiveLocation

class LocationService:

    @classmethod
    def fetch_location(cls, session):

        result = cls.get_location(session.driver_mobile)

        if not result.get("success"):
            return result

        response = result["response"]

        ApiLog.objects.create(
            api_name="Location API",
            request_url=f"{settings.TELENITY_LOCATION_API}/{session.driver_mobile}",
            request_method="GET",
            response_code=result["status_code"],
            response_body=response
        )

        terminals = response.get("terminalLocation", [])

        if not terminals:
            return {
                "success": False,
                "message": "Location not available."
            }

        terminal = terminals[0]

        session.entity_id = terminal.get("entityId", session.entity_id)
        session.location_status = terminal.get("locationRetrievalStatus")

        # Use your existing field
        session.tracking_enabled = terminal.get("tracked", False)

        current = terminal.get("currentLocation")

        if current:

            session.latitude = current.get("latitude")
            session.longitude = current.get("longitude")
            session.last_location = current.get("detailedAddress")

            timestamp = current.get("timestamp")

            if timestamp:
                dt = parse_datetime(timestamp.replace(" ", "T", 1))
                if dt:
                    session.last_updated = dt

            session.status = "active"

            LiveLocation.objects.create(
                session=session,
                tracked=True,
                location_status=terminal.get("locationRetrievalStatus"),
                latitude=current.get("latitude"),
                longitude=current.get("longitude"),
                accuracy=current.get("accuracy", 0),
                address=current.get("detailedAddress", ""),
                location_name=current.get("detailedAddress", ""),
                received_at=session.last_updated,
            )

        else:

            session.status = "pending"

        session.save()

        return {
            "success": True,
            "response": response
        }
    @classmethod
    def get_location(cls, mobile):

        # -----------------------------------------
        # Get Tracking Token
        # -----------------------------------------

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):
            return auth

        token = auth["token"]

        # -----------------------------------------
        # Mobile Format
        # -----------------------------------------

        mobile = str(mobile).strip()

        if mobile.startswith("+91"):
            mobile = mobile.replace("+91", "")

        if not mobile.startswith("91"):
            mobile = "91" + mobile

        # -----------------------------------------
        # URL
        # -----------------------------------------

        url = f"{settings.TELENITY_LOCATION_API}/{mobile}?lastResult=True"

        headers = {
            "Token": token,
            "Content-Type": "application/json"
        }

        print("\n")
        print("=" * 80)
        print("LOCATION API REQUEST")
        print("=" * 80)
        print("URL :", url)
        print("Headers :", headers)
        print("=" * 80)

        try:

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30
            )

            print("\n")
            print("=" * 80)
            print("LOCATION API RESPONSE")
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

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response_data
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