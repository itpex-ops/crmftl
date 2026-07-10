import requests

from django.conf import settings

from .auth_service import TrackingAuthService

from live_tracking.models import (
    TrackingSession,
    ApiLog,
)


class ImportService:

    @classmethod
    def import_driver(cls, vehicle):

        # -------------------------------------------------------
        # GET TRACKING ACCESS TOKEN
        # -------------------------------------------------------

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):
            return auth

        access_token = auth["token"]

        # -------------------------------------------------------
        # IMPORT API URL
        # -------------------------------------------------------

        url = settings.TELENITY_IMPORT_API

        # -------------------------------------------------------
        # HEADERS
        # -------------------------------------------------------

        headers = {
            "Token": access_token,
            "Content-Type": "application/json"
        }

        # -------------------------------------------------------
        # MOBILE FORMAT
        # -------------------------------------------------------

        mobile = str(vehicle.driver_number).strip()

        mobile = mobile.replace(" ", "")

        if mobile.startswith("+91"):
            mobile = mobile[3:]

        if mobile.startswith("91") and len(mobile) == 12:
            pass

        elif len(mobile) == 10:
            mobile = "91" + mobile

        else:
            return {
                "success": False,
                "message": "Invalid Driver Mobile Number."
            }

        # -------------------------------------------------------
        # REQUEST PAYLOAD
        # -------------------------------------------------------

        payload = {
            "entityImportList": [
                {
                    "firstName": "Driver",
                    "lastName": vehicle.vehicle_number,
                    "msisdn": mobile
                }
            ]
        }

        print("\n" + "=" * 80)
        print("TELENITY IMPORT REQUEST")
        print("=" * 80)
        print("URL :", url)
        print("HEADERS :", headers)
        print("PAYLOAD :", payload)
        print("=" * 80)

        try:

            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )

            # -------------------------------------------------------
            # SAFE RESPONSE
            # -------------------------------------------------------

            try:
                response_data = response.json()

            except Exception:

                response_data = {
                    "raw_response": response.text
                }

            # -------------------------------------------------------
            # MASK TOKEN
            # -------------------------------------------------------

            masked_headers = headers.copy()

            if "Token" in masked_headers:

                token = masked_headers["Token"]

                if len(token) > 12:
                    masked_headers["Token"] = (
                        token[:8] + "********"
                    )

            # -------------------------------------------------------
            # SAVE API LOG
            # -------------------------------------------------------

            ApiLog.objects.create(

                api_name="Import API",

                request_url=url,

                request_method="POST",

                request_headers=masked_headers,

                request_body=payload,

                response_code=response.status_code,

                response_body=response_data

            )

            print("\n" + "=" * 80)
            print("TELENITY IMPORT RESPONSE")
            print("=" * 80)
            print("STATUS :", response.status_code)
            print("BODY :", response_data)
            print("=" * 80)

            # -------------------------------------------------------
            # SUCCESS
            # -------------------------------------------------------

            if response.status_code == 200:

                success_list = response_data.get("successList") or []

                if len(success_list) == 0:

                    return {
                        "success": False,
                        "message": "Import succeeded but successList is empty."
                    }

                item = success_list[0]

                session, created = TrackingSession.objects.get_or_create(
                    vehicle=vehicle
                )

                session.driver_mobile = mobile

                session.tracking_reference = vehicle.ftl_no

                session.entity_id = item.get("entityId")

                session.status = "pending"

                session.consent_received = False

                session.save()

                return {
                    "success": True,
                    "session": session,
                    "response": response_data
                }

            # -------------------------------------------------------
            # FAILED
            # -------------------------------------------------------

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