import requests
from django.conf import settings
from onepage_order.models import TrackingSession, ApiLog
from onepage_order.services.consent_auth_service import ConsentAuthService
from onepage_order.services.modify_service import ModifyService

class ConsentService:

    # =========================================================
    # MOBILE FORMAT
    # =========================================================

    @staticmethod
    def normalize_mobile(mobile):
        """
        Convert Indian mobile number into:

            91XXXXXXXXXX

        Accepted examples:

            +919876543210
            919876543210
            9876543210
            00919876543210

        Returns:
            91XXXXXXXXXX
            or None for invalid number.
        """

        mobile = str(mobile or "").strip()

        # Remove common formatting
        mobile = (
            mobile
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        # +91XXXXXXXXXX
        if mobile.startswith("+91"):
            mobile = mobile[3:]

        # 0091XXXXXXXXXX
        elif mobile.startswith("0091"):
            mobile = mobile[4:]

        # 91XXXXXXXXXX
        elif mobile.startswith("91") and len(mobile) == 12:
            mobile = mobile[2:]

        # Must be exactly 10 digits
        if len(mobile) != 10 or not mobile.isdigit():
            return None

        return f"91{mobile}"

    # =========================================================
    # SEND CONSENT
    # =========================================================

    @classmethod
    def onepageorder_send_consent(cls, session):

        if not session:

            return {
                "success": False,
                "message": "Tracking session not found.",
            }

        # ---------------------------------------------------------
        # Get Consent API token
        # ---------------------------------------------------------

        auth = ConsentAuthService.get_consent_token()

        if not auth.get("success"):
            return auth

        bearer_token = auth.get("token")

        if not bearer_token:

            return {
                "success": False,
                "message": (
                    "Consent API bearer token not available."
                ),
            }

        # ---------------------------------------------------------
        # Mobile
        # ---------------------------------------------------------

        mobile = cls.normalize_mobile(
            session.driver_mobile
        )

        if not mobile:

            return {
                "success": False,
                "message": (
                    "Invalid driver mobile number."
                ),
            }

        # ---------------------------------------------------------
        # API URL
        # ---------------------------------------------------------

        url = getattr(
            settings,
            "TELENITY_CONSENT_API",
            "",
        )

        if not url:

            return {
                "success": False,
                "message": (
                    "TELENITY_CONSENT_API "
                    "is not configured."
                ),
            }

        # ---------------------------------------------------------
        # Headers
        # ---------------------------------------------------------

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        # ---------------------------------------------------------
        # Payload
        # ---------------------------------------------------------

        payload = {
            "address": f"tel:+{mobile}",
        }

        try:

            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            # -----------------------------------------------------
            # Response
            # -----------------------------------------------------

            try:
                response_data = response.json()

            except ValueError:
                response_data = {
                    "raw_response": response.text
                }

            # -----------------------------------------------------
            # API LOG
            # -----------------------------------------------------

            try:

                ApiLog.objects.create(
                    api_name="Consent API",
                    request_url=url,
                    request_method="POST",
                    request_headers={
                        "Authorization": "Bearer ********",
                    },
                    request_body=payload,
                    response_code=response.status_code,
                    response_body=response_data,
                )

            except Exception:
                pass

            # -----------------------------------------------------
            # SUCCESS
            # -----------------------------------------------------

            if response.status_code in (
                200,
                201,
                202,
            ):

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
                    "message": (
                        "Consent SMS sent successfully."
                    ),
                    "response": response_data,
                }

            # -----------------------------------------------------
            # FAILURE
            # -----------------------------------------------------

            return {
                "success": False,
                "status_code": response.status_code,
                "message": (
                    "Consent API request failed."
                ),
                "response": response_data,
            }

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Connection timeout while contacting "
                    "Telenity Consent API."
                ),
            }

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "message": (
                    "Unable to connect to "
                    "Telenity Consent API."
                ),
            }

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": (
                    f"Consent API request failed: {exc}"
                ),
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
    def onepageorder_check_consent(cls, session):

        if not session:

            return {
                "success": False,
                "message": "Tracking session not found.",
            }

        # ---------------------------------------------------------
        # Get Consent API token
        # ---------------------------------------------------------

        auth = ConsentAuthService.get_consent_token()

        if not auth.get("success"):
            return auth

        bearer_token = auth.get("token")

        if not bearer_token:

            return {
                "success": False,
                "message": (
                    "Consent API bearer token not available."
                ),
            }

        # ---------------------------------------------------------
        # Mobile
        # ---------------------------------------------------------

        mobile = cls.normalize_mobile(
            session.driver_mobile
        )

        if not mobile:

            return {
                "success": False,
                "message": (
                    "Invalid driver mobile number."
                ),
            }

        # ---------------------------------------------------------
        # API URL
        # ---------------------------------------------------------

        base_url = getattr(
            settings,
            "TELENITY_CONSENT_CHECK_API",
            "",
        )

        if not base_url:

            return {
                "success": False,
                "message": (
                    "TELENITY_CONSENT_CHECK_API "
                    "is not configured."
                ),
            }

        url = (
            f"{base_url}"
            f"?address=tel:+{mobile}"
        )

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "*/*",
        }

        try:

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30,
            )

            # -----------------------------------------------------
            # Response
            # -----------------------------------------------------

            try:
                response_data = response.json()

            except ValueError:
                response_data = {
                    "raw_response": response.text
                }

            # -----------------------------------------------------
            # API LOG
            # -----------------------------------------------------

            try:

                ApiLog.objects.create(
                    api_name="Consent Check API",
                    request_url=url,
                    request_method="GET",
                    request_headers={
                        "Authorization": "Bearer ********",
                    },
                    request_body=None,
                    response_code=response.status_code,
                    response_body=response_data,
                )

            except Exception:
                pass

            # -----------------------------------------------------
            # HTTP ERROR
            # -----------------------------------------------------

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Consent check API failed."
                    ),
                    "response": response_data,
                }

            # -----------------------------------------------------
            # CONSENT OBJECT
            # -----------------------------------------------------

            consent = response_data.get(
                "Consent",
                {},
            )

            if not isinstance(consent, dict):

                return {
                    "success": False,
                    "message": (
                        "Invalid Consent API response format."
                    ),
                    "response": response_data,
                }

            # -----------------------------------------------------
            # STATUS
            # -----------------------------------------------------

            status = str(
                consent.get("status", "")
            ).strip().lower()

            # =====================================================
            # APPROVED
            # =====================================================

            if status in (
                "allowed",
                "consent_approved",
                "approved",
                "accepted",
            ):

                session.consent_received = True
                session.status = "consent_received"

                # Save consent reference if API provides one
                consent_reference = (
                    consent.get("reference")
                    or consent.get("consentReference")
                    or consent.get("consent_reference")
                )

                if consent_reference:
                    session.consent_reference = (
                        str(consent_reference)
                    )

                update_fields = [
                    "consent_received",
                    "status",
                ]

                if consent_reference:
                    update_fields.append(
                        "consent_reference"
                    )

                session.save(
                    update_fields=update_fields
                )

                # -------------------------------------------------
                # Start tracking through Modify API
                # -------------------------------------------------

                modify = ModifyService.start_tracking(
                    session
                )

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
                        "message": (
                            "Consent approved and "
                            "tracking started."
                        ),
                        "response": response_data,
                        "modify_response": modify,
                    }

                # -------------------------------------------------
                # MODIFY FAILED
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
                    "message": (
                        "Consent approved, but tracking "
                        "could not be started."
                    ),
                    "response": response_data,
                    "modify_response": modify,
                }

            # =====================================================
            # PENDING
            # =====================================================

            if status in (
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
                    "message": (
                        "Consent is still pending."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # LICENSE HOLD
            # =====================================================

            if status == "license_hold":

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
                    "message": (
                        "Tracking license is on hold."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # EXPIRED
            # =====================================================

            if status == "expired":

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
                    "message": (
                        "Tracking consent has expired."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # UNKNOWN STATUS
            # =====================================================

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
                "message": (
                    "Unknown consent status received "
                    "from Telenity."
                ),
                "response": response_data,
            }

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Connection timeout while "
                    "checking consent."
                ),
            }

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "message": (
                    "Unable to connect to "
                    "Telenity Consent API."
                ),
            }

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": (
                    f"Consent check request failed: {exc}"
                ),
            }

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc),
            }