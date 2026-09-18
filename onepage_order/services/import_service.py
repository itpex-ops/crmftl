import requests

from django.conf import settings

from onepage_order.models import TrackingSession, ApiLog
from onepage_order.services.auth_service import TrackingAuthService


class ImportService:

    @staticmethod
    def normalize_mobile(mobile):
        """
        Convert Indian 10-digit mobile number to 91XXXXXXXXXX.
        """

        if not mobile:
            return None

        mobile = str(mobile).strip()

        # Remove common formatting
        mobile = mobile.replace("+", "")
        mobile = mobile.replace(" ", "")
        mobile = mobile.replace("-", "")

        # 0091XXXXXXXXXX
        if mobile.startswith("0091"):
            mobile = mobile[4:]

        # 91XXXXXXXXXX
        elif mobile.startswith("91") and len(mobile) == 12:
            mobile = mobile[2:]

        # Must finally be exactly 10 digits
        if len(mobile) != 10 or not mobile.isdigit():
            return None

        return f"91{mobile}"

    # =============================================================
    # IMPORT DRIVER
    # =============================================================

    @classmethod
    def import_driver(cls, order):

        # ---------------------------------------------------------
        # Validate driver number
        # ---------------------------------------------------------

        mobile = cls.normalize_mobile(
            order.driver_number
        )

        if not mobile:

            return {
                "success": False,
                "message": (
                    "Invalid driver mobile number. "
                    "Enter a valid 10-digit mobile number."
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
        # API URL
        # ---------------------------------------------------------

        url = getattr(
            settings,
            "TELENITY_IMPORT_API",
            "",
        )

        if not url:

            return {
                "success": False,
                "message": (
                    "TELENITY_IMPORT_API "
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
            "entityImportList": [
                {
                    "firstName": "Driver",
                    "lastName": (
                        order.vehicle_number
                        or "Vehicle"
                    ),
                    "msisdn": mobile,
                }
            ]
        }

        try:

            # =====================================================
            # CALL IMPORT API
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
                    api_name="IMPORT",
                    request_url=url,
                    request_method="POST",
                    request_json=payload,
                    response_json=response_data,
                    response_code=response.status_code,
                )

            except Exception:
                # Logging failure must not break the API flow.
                pass

            # =====================================================
            # HTTP ERROR
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
                        "Driver import API failed."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # SUCCESS RESPONSE
            # =====================================================

            success_list = response_data.get(
                "successList"
            )

            # -----------------------------------------------------
            # IMPORTANT
            #
            # Do not create TrackingSession if Telenity has not
            # actually returned an imported entity.
            # -----------------------------------------------------

            if not success_list:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Import API succeeded, but "
                        "successList is empty."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # FIRST IMPORTED ENTITY
            # =====================================================

            item = success_list[0]

            entity_id = item.get("entityId")

            if not entity_id:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Import API returned successList "
                        "but entityId was not found."
                    ),
                    "response": response_data,
                    "success_item": item,
                }

            # =====================================================
            # CREATE / GET TRACKING SESSION
            # =====================================================

            session, created = (
                TrackingSession.objects.get_or_create(
                    order=order,
                    defaults={
                        "driver_mobile": mobile,
                        "tracking_reference": (
                            order.trip_number
                        ),
                        "entity_id": entity_id,
                        "status": "imported",
                        "consent_received": False,
                        "tracking_enabled": False,
                    },
                )
            )

            # =====================================================
            # UPDATE EXISTING SESSION
            # =====================================================

            if not created:

                session.driver_mobile = mobile

                session.tracking_reference = (
                    order.trip_number
                )

                session.entity_id = entity_id

                session.status = "imported"

                session.consent_received = False

                session.tracking_enabled = False

                session.save(
                    update_fields=[
                        "driver_mobile",
                        "tracking_reference",
                        "entity_id",
                        "status",
                        "consent_received",
                        "tracking_enabled",
                    ]
                )

            # =====================================================
            # SUCCESS
            # =====================================================

            return {
                "success": True,
                "status_code": response.status_code,
                "message": (
                    "Driver imported successfully."
                ),
                "session": session,
                "entity_id": entity_id,
                "mobile": mobile,
                "response": response_data,
            }

        # =========================================================
        # TIMEOUT
        # =========================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Driver import API request timed out."
                ),
            }

        # =========================================================
        # CONNECTION ERROR
        # =========================================================

        except requests.exceptions.ConnectionError as exc:

            return {
                "success": False,
                "message": (
                    "Unable to connect to driver "
                    "import API."
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
                    "Driver import API request failed."
                ),
                "error": str(exc),
            }

        # =========================================================
        # UNEXPECTED ERROR
        # =========================================================

        except Exception as exc:

            return {
                "success": False,
                "message": (
                    "Unexpected error while importing driver."
                ),
                "error": str(exc),
            }