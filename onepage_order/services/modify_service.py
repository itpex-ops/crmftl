import requests

from django.conf import settings

from onepage_order.models import TrackingSession, ApiLog
from onepage_order.services.auth_service import TrackingAuthService


class ModifyService:

    # =========================================================
    # START TRACKING
    # =========================================================

    @classmethod
    def start_tracking(cls, session):

        if not session:

            return {
                "success": False,
                "message": "Tracking session not found.",
            }

        # ---------------------------------------------------------
        # Entity ID
        # ---------------------------------------------------------

        entity_id = session.entity_id

        if not entity_id:

            return {
                "success": False,
                "message": (
                    "Telenity entity ID is not available."
                ),
            }

        # ---------------------------------------------------------
        # Tracking authentication
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
        # Modify API URL
        # ---------------------------------------------------------

        base_url = getattr(
            settings,
            "TELENITY_MODIFY_API",
            "",
        )

        if not base_url:

            return {
                "success": False,
                "message": (
                    "TELENITY_MODIFY_API "
                    "is not configured."
                ),
            }

        # ---------------------------------------------------------
        # URL
        # ---------------------------------------------------------

        url = f"{base_url}/{entity_id}"

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
            "isActive": True,
            "isTracked": True,
        }

        try:

            response = requests.put(
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

            # -----------------------------------------------------
            # API LOG
            # -----------------------------------------------------

            try:

                ApiLog.objects.create(
                    api_name="Modify API",
                    request_url=url,
                    request_method="PUT",
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
            # SUCCESS
            # =====================================================

            if response.status_code in (
                200,
                201,
                202,
            ):

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
                    "status": "waiting_location",
                    "tracking_enabled": True,
                    "message": (
                        "Tracking activated successfully."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # FAILURE
            # =====================================================

            return {
                "success": False,
                "status_code": response.status_code,
                "message": (
                    "Telenity Modify API failed."
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
                    "Modify API request timed out."
                ),
            }

        # =========================================================
        # CONNECTION ERROR
        # =========================================================

        except requests.exceptions.ConnectionError as exc:

            return {
                "success": False,
                "message": (
                    "Unable to connect to Telenity "
                    "Modify API."
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
                    f"Modify API request failed: {exc}"
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