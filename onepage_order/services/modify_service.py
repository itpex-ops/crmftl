import requests

from django.conf import settings

from .auth_service import TrackingAuthService

from ..models import ApiLog


class ModifyService:

    # =========================================================
    # START TRACKING
    # =========================================================

    @classmethod
    def start_tracking(cls, session):

        # -----------------------------------------------------
        # VALIDATE SESSION
        # -----------------------------------------------------

        if not session:
            return {
                "success": False,
                "message": "Tracking session not found."
            }

        # -----------------------------------------------------
        # GET TRACKING ACCESS TOKEN
        # -----------------------------------------------------

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):
            return auth

        token = auth.get("token")

        if not token:
            return {
                "success": False,
                "message": "Tracking access token not available."
            }

        # -----------------------------------------------------
        # ENTITY ID
        # -----------------------------------------------------

        if not session.entity_id:

            return {
                "success": False,
                "message": "Entity ID is missing."
            }

        # -----------------------------------------------------
        # MODIFY API URL
        # -----------------------------------------------------

        base_url = getattr(
            settings,
            "TELENITY_MODIFY_API",
            ""
        )

        if not base_url:

            return {
                "success": False,
                "message": "TELENITY_MODIFY_API is not configured."
            }

        url = (
            f"{base_url.rstrip('/')}"
            f"/{session.entity_id}"
        )

        # -----------------------------------------------------
        # HEADERS
        # -----------------------------------------------------

        headers = {
            "Token": token,
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        # -----------------------------------------------------
        # PAYLOAD
        # -----------------------------------------------------

        payload = {
            "isActive": True,
            "isTracked": True,
        }

        # -----------------------------------------------------
        # MASK TOKEN
        # -----------------------------------------------------

        masked_token = "********"

        if len(token) > 12:

            masked_token = (
                token[:8]
                + "********"
            )

        # -----------------------------------------------------
        # DEBUG REQUEST
        # -----------------------------------------------------

        print()
        print("=" * 80)
        print("MODIFY API REQUEST")
        print("=" * 80)
        print("URL :", url)
        print(
            "Headers :",
            {
                "Token": masked_token,
                "Content-Type": "application/json",
                "Accept": "*/*",
            }
        )
        print("Payload :", payload)
        print("=" * 80)

        try:

            # -------------------------------------------------
            # API REQUEST
            # -------------------------------------------------

            response = requests.put(
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
            # API LOG
            # -------------------------------------------------

            ApiLog.objects.create(
                api_name="Modify API",
                request_url=url,
                request_method="PUT",
                request_headers={
                    "Token": masked_token,
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                },
                request_body=payload,
                response_code=response.status_code,
                response_body=response_data,
            )

            # -------------------------------------------------
            # DEBUG RESPONSE
            # -------------------------------------------------

            print()
            print("=" * 80)
            print("MODIFY API RESPONSE")
            print("=" * 80)
            print("Status   :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            # =================================================
            # SUCCESS
            # =================================================

            if response.status_code in (200, 201, 202):

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
                    "response": response_data,
                }

            # =================================================
            # FAILURE
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
                "message": (
                    "Connection timeout while "
                    "contacting Telenity Modify API."
                )
            }

        # =====================================================
        # CONNECTION ERROR
        # =====================================================

        except requests.exceptions.ConnectionError:

            return {
                "success": False,
                "message": (
                    "Unable to connect to Telenity Server."
                )
            }

        # =====================================================
        # REQUEST ERROR
        # =====================================================

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": (
                    f"Modify API request failed: {exc}"
                )
            }

        # =====================================================
        # OTHER ERROR
        # =====================================================

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc)
            }