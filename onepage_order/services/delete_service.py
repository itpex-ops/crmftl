import requests

from django.conf import settings

from onepage_order.models import TrackingSession, ApiLog
from onepage_order.services.auth_service import TrackingAuthService


class DeleteService:

    # =========================================================
    # MOBILE FORMAT
    # =========================================================

    @staticmethod
    def normalize_mobile(mobile):
        """
        Convert Indian mobile number to:

            91XXXXXXXXXX
        """

        mobile = str(mobile or "").strip()

        mobile = (
            mobile
            .replace("+", "")
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if mobile.startswith("0091"):
            mobile = mobile[4:]

        elif mobile.startswith("91") and len(mobile) == 12:
            mobile = mobile[2:]

        if len(mobile) != 10 or not mobile.isdigit():
            return None

        return f"91{mobile}"

    # =========================================================
    # DELETE TRACKING
    # =========================================================

    @classmethod
    def delete_tracking(cls, session):

        if not session:

            return {
                "success": False,
                "message": "Tracking session not found.",
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
        # Get tracking token
        # ---------------------------------------------------------

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):

            return {
                "success": False,
                "message": auth.get(
                    "message",
                    "Unable to get tracking authentication token.",
                ),
                "auth_response": auth,
            }

        token = auth.get("token")

        if not token:

            return {
                "success": False,
                "message": (
                    "Tracking authentication succeeded "
                    "but token was not returned."
                ),
            }

        # ---------------------------------------------------------
        # Delete API
        # ---------------------------------------------------------

        url = getattr(
            settings,
            "TELENITY_DELETE_API",
            "",
        )

        if not url:

            return {
                "success": False,
                "message": (
                    "TELENITY_DELETE_API "
                    "is not configured."
                ),
            }

        # ---------------------------------------------------------
        # Headers
        # ---------------------------------------------------------

        headers = {
            "Token": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # ---------------------------------------------------------
        # Payload
        # ---------------------------------------------------------

        payload = {
            "msisdnList": [
                mobile,
            ]
        }

        try:

            # =====================================================
            # CALL DELETE API
            # =====================================================

            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            # -----------------------------------------------------
            # Parse response
            # -----------------------------------------------------

            try:

                response_data = response.json()

            except ValueError:

                response_data = {
                    "raw_response": response.text
                }

            # =====================================================
            # API LOG
            # =====================================================

            try:

                ApiLog.objects.create(
                    api_name="Delete API",
                    request_url=url,
                    request_method="POST",
                    request_headers={
                        "Token": "********",
                    },
                    request_body=payload,
                    response_code=response.status_code,
                    response_body=response_data,
                )

            except Exception:
                pass

            # =====================================================
            # HTTP CHECK
            # =====================================================

            if response.status_code not in (
                200,
                201,
                202,
            ):

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Telenity Delete API failed."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # API SUCCESS CHECK
            # =====================================================

            if (
                isinstance(response_data, dict)
                and response_data.get("success") is False
            ):

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Telenity Delete API returned "
                        "a failure response."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # LOCAL SESSION UPDATE
            # =====================================================

            session.status = "deleted"
            session.tracking_enabled = False
            session.consent_received = False

            session.latitude = None
            session.longitude = None
            session.last_location = None
            session.last_updated = None
            session.location_status = None

            session.entity_id = None
            session.consent_reference = None

            session.save(
                update_fields=[
                    "status",
                    "tracking_enabled",
                    "consent_received",
                    "latitude",
                    "longitude",
                    "last_location",
                    "last_updated",
                    "location_status",
                    "entity_id",
                    "consent_reference",
                ]
            )

            # =====================================================
            # SUCCESS
            # =====================================================

            return {
                "success": True,
                "status": "deleted",
                "message": (
                    "Tracking deleted successfully."
                ),
                "response": response_data,
            }

        # =========================================================
        # TIMEOUT
        # =========================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Delete API request timed out."
                ),
            }

        # =========================================================
        # CONNECTION ERROR
        # =========================================================

        except requests.exceptions.ConnectionError as exc:

            return {
                "success": False,
                "message": (
                    "Unable to connect to "
                    "Telenity Delete API."
                ),
                "error": str(exc),
            }

        # =========================================================
        # REQUEST ERROR
        # =========================================================

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": (
                    f"Delete API request failed: {exc}"
                ),
            }

        # =========================================================
        # UNEXPECTED ERROR
        # =========================================================

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc),
            }