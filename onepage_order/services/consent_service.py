import requests

from django.conf import settings

from ..models import TrackingSession, ApiLog

from .consent_auth_service import ConsentAuthService
from .modify_service import ModifyService


class ConsentService:
    """
    Handles Telenity Consent API operations.

    Flow:

        Import Driver
             ↓
        Send Consent SMS
             ↓
        Check Consent
             ↓
        Consent Approved
             ↓
        Start Tracking / Modify API
             ↓
        Waiting Location
             ↓
        Location Received
             ↓
        Active
    """

    # =========================================================
    # MOBILE FORMAT
    # =========================================================

    @staticmethod
    def normalize_mobile(mobile):
        """
        Convert Indian mobile number into:

            91XXXXXXXXXX

        Examples:

            +919876543210
            919876543210
            9876543210

        all become:

            919876543210
        """

        mobile = str(mobile or "").strip()

        # Remove spaces, hyphens and brackets
        mobile = (
            mobile
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if mobile.startswith("+91"):
            mobile = mobile[3:]

        elif mobile.startswith("0091"):
            mobile = mobile[4:]

        elif mobile.startswith("91") and len(mobile) == 12:
            mobile = mobile[2:]

        # Final format
        if not mobile.startswith("91"):
            mobile = "91" + mobile

        return mobile

    # =========================================================
    # SEND CONSENT
    # =========================================================

    @classmethod
    def send_consent(cls, session):

        if not session:
            return {
                "success": False,
                "message": "Tracking session not found."
            }

        auth = ConsentAuthService.get_consent_token()

        if not auth.get("success"):
            return auth

        bearer_token = auth.get("token")

        if not bearer_token:
            return {
                "success": False,
                "message": "Consent API bearer token not available."
            }

        mobile = cls.normalize_mobile(session.driver_mobile)

        if not mobile or len(mobile) != 12:
            return {
                "success": False,
                "message": "Invalid driver mobile number."
            }

        url = getattr(settings, "TELENITY_CONSENT_API", "")

        if not url:
            return {
                "success": False,
                "message": "TELENITY_CONSENT_API is not configured."
            }

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        payload = {
            "address": f"tel:+{mobile}"
        }

        print()
        print("=" * 80)
        print("CONSENT REQUEST")
        print("=" * 80)
        print("URL     :", url)
        print("Payload :", payload)
        print("=" * 80)

        try:

            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            try:
                response_data = response.json()

            except ValueError:
                response_data = {
                    "raw_response": response.text
                }

            # -------------------------------------------------
            # API LOG
            # -------------------------------------------------

            ApiLog.objects.create(
                api_name="Consent API",
                request_url=url,
                request_method="POST",
                request_headers={
                    "Authorization": "Bearer ********"
                },
                request_body=payload,
                response_code=response.status_code,
                response_body=response_data,
            )

            print("=" * 80)
            print("CONSENT RESPONSE")
            print("=" * 80)
            print("Status   :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            if response.status_code in (200, 201, 202):

                session.status = "sms_sent"
                session.consent_received = False
                session.save(
                    update_fields=[
                        "status",
                        "consent_received",
                    ]
                )

                return {
                    "success": True,
                    "status": "sms_sent",
                    "response": response_data,
                }

            # -------------------------------------------------
            # FAILURE
            # -------------------------------------------------

            return {
                "success": False,
                "status_code": response.status_code,
                "message": response_data,
            }

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": "Connection timeout while contacting Telenity Consent API."
            }

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "message": "Unable to connect to Telenity Consent API."
            }

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": f"Consent API request failed: {exc}"
            }

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc),
            }

    # =========================================================
    # CHECK CONSENT
    # =========================================================

    @classmethod
    def check_consent(cls, session):

        if not session:
            return {
                "success": False,
                "message": "Tracking session not found."
            }

        auth = ConsentAuthService.get_consent_token()

        if not auth.get("success"):
            return auth

        bearer_token = auth.get("token")

        if not bearer_token:
            return {
                "success": False,
                "message": "Consent API bearer token not available."
            }

        # -------------------------------------------------
        # MOBILE
        # -------------------------------------------------

        mobile = cls.normalize_mobile(session.driver_mobile)

        if not mobile or len(mobile) != 12:
            return {
                "success": False,
                "message": "Invalid driver mobile number."
            }

        # -------------------------------------------------
        # URL
        # -------------------------------------------------

        base_url = getattr(
            settings,
            "TELENITY_CONSENT_CHECK_API",
            ""
        )

        if not base_url:
            return {
                "success": False,
                "message": "TELENITY_CONSENT_CHECK_API is not configured."
            }

        url = f"{base_url}?address=tel:+{mobile}"

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "*/*",
        }

        print()
        print("=" * 80)
        print("CONSENT CHECK REQUEST")
        print("=" * 80)
        print("URL :", url)
        print(
            "Headers :",
            {
                "Authorization": "Bearer ********"
            }
        )
        print("=" * 80)

        try:

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30,
            )

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            try:
                response_data = response.json()

            except ValueError:
                response_data = {
                    "raw_response": response.text
                }

            print("=" * 80)
            print("RAW CONSENT RESPONSE")
            print("=" * 80)
            print("Status   :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            # -------------------------------------------------
            # API LOG
            # -------------------------------------------------

            ApiLog.objects.create(
                api_name="Consent Check API",
                request_url=url,
                request_method="GET",
                request_headers={
                    "Authorization": "Bearer ********"
                },
                request_body=None,
                response_code=response.status_code,
                response_body=response_data,
            )

            # -------------------------------------------------
            # HTTP ERROR
            # -------------------------------------------------

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": response_data,
                }

            # -------------------------------------------------
            # CONSENT OBJECT
            # -------------------------------------------------

            consent = response_data.get("Consent", {})

            print("CONSENT OBJECT :", consent)

            if not isinstance(consent, dict):

                return {
                    "success": False,
                    "message": "Invalid Consent API response format.",
                    "response": response_data,
                }

            # -------------------------------------------------
            # STATUS
            # -------------------------------------------------

            status = str(
                consent.get("status", "")
            ).strip().lower()

            print("CONSENT STATUS :", status)

            # =================================================
            # APPROVED
            # =================================================

            if status in (
                "allowed",
                "consent_approved",
                "approved",
                "accepted",
            ):

                session.consent_received = True
                session.status = "consent_received"

                session.save(
                    update_fields=[
                        "consent_received",
                        "status",
                    ]
                )

                print("=" * 80)
                print("CONSENT APPROVED")
                print("=" * 80)

                # -------------------------------------------------
                # START TRACKING
                # -------------------------------------------------

                modify = ModifyService.start_tracking(session)

                print("=" * 80)
                print("MODIFY RESULT")
                print("=" * 80)
                print(modify)
                print("=" * 80)

                if modify.get("success"):

                    session.tracking_enabled = True
                    session.status = "waiting_location"

                    session.save(
                        update_fields=[
                            "tracking_enabled",
                            "status",
                        ]
                    )

                    return {
                        "success": True,
                        "status": status,
                        "tracking_started": True,
                        "response": response_data,
                        "modify_response": modify,
                    }

                # -------------------------------------------------
                # CONSENT APPROVED BUT MODIFY FAILED
                # -------------------------------------------------

                session.tracking_enabled = False
                session.status = "error"

                session.save(
                    update_fields=[
                        "tracking_enabled",
                        "status",
                    ]
                )

                return {
                    "success": False,
                    "status": status,
                    "tracking_started": False,
                    "message": "Consent approved, but tracking could not be started.",
                    "response": response_data,
                    "modify_response": modify,
                }

            # =================================================
            # PENDING
            # =================================================

            elif status in (
                "pending",
                "requested",
                "waiting",
                "sms_sent",
            ):

                session.consent_received = False
                session.status = "sms_sent"

                session.save(
                    update_fields=[
                        "consent_received",
                        "status",
                    ]
                )

                return {
                    "success": True,
                    "status": status,
                    "tracking_started": False,
                    "response": response_data,
                }

            # =================================================
            # LICENSE HOLD
            # =================================================

            elif status == "license_hold":

                session.consent_received = False
                session.status = "license_hold"

                session.save(
                    update_fields=[
                        "consent_received",
                        "status",
                    ]
                )

                return {
                    "success": True,
                    "status": status,
                    "tracking_started": False,
                    "response": response_data,
                }

            # =================================================
            # EXPIRED
            # =================================================

            elif status == "expired":

                session.consent_received = False
                session.status = "expired"

                session.save(
                    update_fields=[
                        "consent_received",
                        "status",
                    ]
                )

                return {
                    "success": True,
                    "status": status,
                    "tracking_started": False,
                    "response": response_data,
                }

            # =================================================
            # UNKNOWN STATUS
            # =================================================

            else:

                session.consent_received = False
                session.status = "error"

                session.save(
                    update_fields=[
                        "consent_received",
                        "status",
                    ]
                )

                return {
                    "success": True,
                    "status": status,
                    "tracking_started": False,
                    "message": "Unknown consent status received from Telenity.",
                    "response": response_data,
                }

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": "Connection timeout while checking consent."
            }

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "message": "Unable to connect to Telenity Consent API."
            }

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": f"Consent check request failed: {exc}"
            }

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc)
            }