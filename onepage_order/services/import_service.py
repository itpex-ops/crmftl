import requests

from django.conf import settings

from .auth_service import TrackingAuthService

from ..models import (
    TrackingSession,
    ApiLog,
)


class ImportService:

    # =========================================================
    # MOBILE NORMALIZATION
    # =========================================================

    @staticmethod
    def normalize_mobile(mobile):
        """
        Convert Indian mobile number to:

            91XXXXXXXXXX

        Accepted:

            9876543210
            919876543210
            +919876543210
            00919876543210
        """

        mobile = str(mobile or "").strip()

        # Remove common separators
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

        # Must now be exactly 10 digits
        if len(mobile) != 10 or not mobile.isdigit():
            return None

        return "91" + mobile

    # =========================================================
    # IMPORT DRIVER
    # =========================================================

    @classmethod
    def import_driver(cls, vehicle):

        if not vehicle:
            return {
                "success": False,
                "message": "Vehicle / Order not found."
            }

        # -----------------------------------------------------
        # GET TRACKING ACCESS TOKEN
        # -----------------------------------------------------

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):
            return auth

        access_token = auth.get("token")

        if not access_token:
            return {
                "success": False,
                "message": "Tracking access token not available."
            }

        # -----------------------------------------------------
        # IMPORT API URL
        # -----------------------------------------------------

        url = getattr(
            settings,
            "TELENITY_IMPORT_API",
            ""
        )

        if not url:
            return {
                "success": False,
                "message": "TELENITY_IMPORT_API is not configured."
            }

        # -----------------------------------------------------
        # MOBILE FORMAT
        # -----------------------------------------------------

        mobile = cls.normalize_mobile(
            vehicle.driver_number
        )

        if not mobile:
            return {
                "success": False,
                "message": "Invalid Driver Mobile Number."
            }

        # -----------------------------------------------------
        # HEADERS
        # -----------------------------------------------------

        headers = {
            "Token": access_token,
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        # -----------------------------------------------------
        # REQUEST PAYLOAD
        # -----------------------------------------------------

        payload = {
            "entityImportList": [
                {
                    "firstName": "Driver",
                    "lastName": vehicle.vehicle_number,
                    "msisdn": mobile,
                }
            ]
        }

        # -----------------------------------------------------
        # SAFE DEBUG OUTPUT
        # -----------------------------------------------------

        masked_token = "********"

        if len(access_token) > 12:
            masked_token = (
                access_token[:8]
                + "********"
            )

        print()
        print("=" * 80)
        print("TELENITY IMPORT REQUEST")
        print("=" * 80)
        print("URL :", url)
        print(
            "HEADERS :",
            {
                "Token": masked_token,
                "Content-Type": "application/json",
                "Accept": "*/*",
            }
        )
        print("PAYLOAD :", payload)
        print("=" * 80)

        try:

            # -------------------------------------------------
            # API REQUEST
            # -------------------------------------------------

            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            # -------------------------------------------------
            # SAFE RESPONSE
            # -------------------------------------------------

            try:
                response_data = response.json()

            except ValueError:
                response_data = {
                    "raw_response": response.text
                }

            # -------------------------------------------------
            # MASK TOKEN FOR API LOG
            # -------------------------------------------------

            masked_headers = {
                "Token": masked_token,
                "Content-Type": "application/json",
                "Accept": "*/*",
            }

            # -------------------------------------------------
            # SAVE API LOG
            # -------------------------------------------------

            ApiLog.objects.create(
                api_name="Import API",
                request_url=url,
                request_method="POST",
                request_headers=masked_headers,
                request_body=payload,
                response_code=response.status_code,
                response_body=response_data,
            )

            # -------------------------------------------------
            # DEBUG RESPONSE
            # -------------------------------------------------

            print()
            print("=" * 80)
            print("TELENITY IMPORT RESPONSE")
            print("=" * 80)
            print("STATUS :", response.status_code)
            print("BODY   :", response_data)
            print("=" * 80)

            # =================================================
            # SUCCESS
            # =================================================

            if response.status_code in (200, 201, 202):

                success_list = (
                    response_data.get("successList")
                    or []
                )

                if not success_list:

                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "message": (
                            "Import API succeeded, "
                            "but successList is empty."
                        ),
                        "response": response_data,
                    }

                item = success_list[0]

                # -------------------------------------------------
                # GET ENTITY ID
                # -------------------------------------------------

                entity_id = item.get("entityId")

                if not entity_id:

                    return {
                        "success": False,
                        "message": (
                            "Import API succeeded, "
                            "but entityId was not returned."
                        ),
                        "response": response_data,
                    }

                # -------------------------------------------------
                # CREATE / UPDATE TRACKING SESSION
                # -------------------------------------------------

                session, created = (
                    TrackingSession.objects.get_or_create(
                        order=vehicle
                    )
                )

                session.driver_mobile = mobile

                session.tracking_reference = (
                    vehicle.ftl_no
                )

                session.entity_id = entity_id

                # IMPORTANT:
                # "pending" is NOT a valid TrackingSession status.
                session.status = "imported"

                session.consent_received = False

                session.tracking_enabled = False

                session.save()

                # -------------------------------------------------
                # RESULT
                # -------------------------------------------------

                return {
                    "success": True,
                    "created": created,
                    "session": session,
                    "entity_id": entity_id,
                    "response": response_data,
                }

            # =================================================
            # FAILED
            # =================================================

            return {
                "success": False,
                "status_code": response.status_code,
                "message": response_data,
            }

        # =====================================================
        # TIMEOUT
        # =====================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": "Connection timeout while contacting Telenity Import API."
            }

        # =====================================================
        # CONNECTION ERROR
        # =====================================================

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "message": "Unable to connect to Telenity Server."
            }

        # =====================================================
        # REQUEST ERROR
        # =====================================================

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": f"Import API request failed: {exc}"
            }

        # =====================================================
        # OTHER ERROR
        # =====================================================

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc)
            }