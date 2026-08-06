import requests

from django.conf import settings

from .consent_auth_service import ConsentAuthService

from live_tracking.models import (
    TrackingSession,
    ApiLog,
)
from .modify_service import ModifyService
class ConsentService:
    @classmethod
    def send_consent(cls, session):
        auth = ConsentAuthService.get_consent_token()

        if not auth.get("success"):
            return auth

        bearer_token = auth["token"]
        mobile = str(session.driver_mobile).strip()

        if mobile.startswith("+91"):
            mobile = mobile.replace("+91", "")

        if not mobile.startswith("91"):
            mobile = "91" + mobile
        url = settings.TELENITY_CONSENT_API

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "address": f"tel:+{mobile}"
        }

        print("\n")
        print("=" * 80)
        print("CONSENT REQUEST")
        print("=" * 80)
        print("URL :", url)
        print("Payload :", payload)
        print("=" * 80)

        try:

            response = requests.post(
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
                api_name="Consent API",
                request_url=url,
                request_method="POST",
                request_headers={
                    "Authorization": "Bearer ********"
                },
                request_body=payload,
                response_code=response.status_code,
                response_body=response_data
            )

            print("=" * 80)
            print("CONSENT RESPONSE")
            print("=" * 80)
            print("Status :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            if response.status_code in (200, 201):

                session.status = "sms_sent"
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

    @classmethod
    def check_consent(cls, session):

        auth = ConsentAuthService.get_consent_token()

        if not auth.get("success"):
            return auth

        bearer_token = auth["token"]

        # -------------------------------------------------
        # MOBILE FORMAT
        # -------------------------------------------------

        mobile = str(session.driver_mobile).strip()

        if mobile.startswith("+91"):
            mobile = mobile.replace("+91", "")

        if not mobile.startswith("91"):
            mobile = "91" + mobile

        # -------------------------------------------------
        # URL
        # -------------------------------------------------

        url = (
            f"{settings.TELENITY_CONSENT_CHECK_API}"
            f"?address=tel:+{mobile}"
        )

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "*/*"
        }

        print("\n")
        print("=" * 80)
        print("CONSENT CHECK REQUEST")
        print("=" * 80)
        print("URL :", url)
        print("Headers :", {
            "Authorization": "Bearer ********"
        })
        print("=" * 80)

        try:

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30
            )

            try:
                response_data = response.json()
                print("RAW CONSENT JSON")
                print(response_data)
            except Exception:
                response_data = {
                    "raw_response": response.text
                }

            ApiLog.objects.create(
                api_name="Consent Check API",
                request_url=url,
                request_method="GET",
                request_headers={
                    "Authorization": "Bearer ********"
                },
                request_body=None,
                response_code=response.status_code,
                response_body=response_data
            )

            print("=" * 80)
            print("CONSENT CHECK RESPONSE")
            print("=" * 80)
            print("Status :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            if response.status_code != 200:

                return {
                    "success": False,
                    "message": response_data
                }

            consent = response_data.get("Consent", {})
            print("CONSENT OBJECT:", consent)

            status = consent.get("status", "").lower()

            print("STATUS:", status)

            if status in ["allowed", "consent_approved"]:

                session.status = "active"
                session.consent_received = True
                session.save()

                modify = ModifyService.start_tracking(session)

                print("=" * 80)
                print("MODIFY RESULT")
                print(modify)
                print("=" * 80)

            elif status == "pending":

                session.status = "pending"
                session.consent_received = False

            elif status == "license_hold":

                session.status = "license_hold"
                session.consent_received = False

            else:

                session.status = "pending"

            session.save()

            return {
                "success": True,
                "status": status,
                "response": response_data
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }