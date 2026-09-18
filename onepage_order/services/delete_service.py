import requests

from django.conf import settings

from .auth_service import TrackingAuthService

from ..models import ApiLog


class DeleteService:

    # =========================================================
    # DELETE TRACKING
    # =========================================================

    @classmethod
    def delete_tracking(cls, session):

        # -----------------------------------------------------
        # VALIDATE SESSION
        # -----------------------------------------------------

        if not session:
            return {
                "success": False,
                "message": "Tracking session not found."
            }

        # -----------------------------------------------------
        # GET TRACKING TOKEN
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
        # MOBILE FORMAT
        # -----------------------------------------------------

        mobile = str(
            session.driver_mobile or ""
        ).strip()

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

        if len(mobile) != 10 or not mobile.isdigit():

            return {
                "success": False,
                "message": "Invalid Driver Mobile Number."
            }

        mobile = "91" + mobile

        # -----------------------------------------------------
        # DELETE API URL
        # -----------------------------------------------------

        url = getattr(
            settings,
            "TELENITY_DELETE_API",
            ""
        )

        if not url:

            return {
                "success": False,
                "message": "TELENITY_DELETE_API is not configured."
            }

        # -----------------------------------------------------
        # HEADERS
        # -----------------------------------------------------

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        # -----------------------------------------------------
        # PAYLOAD
        # -----------------------------------------------------

        payload = {
            "msisdnList": [
                mobile
            ]
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
        print("DELETE API REQUEST")
        print("=" * 80)
        print("URL :", url)
        print(
            "Headers :",
            {
                "Authorization": f"Bearer {masked_token}",
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
            # DEBUG RESPONSE
            # -------------------------------------------------

            print()
            print("=" * 80)
            print("DELETE API RESPONSE")
            print("=" * 80)
            print("Status   :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            # -------------------------------------------------
            # API LOG
            # -------------------------------------------------

            ApiLog.objects.create(
                api_name="Delete API",
                request_url=url,
                request_method="POST",
                request_headers={
                    "Authorization": "Bearer ********",
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                },
                request_body=payload,
                response_code=response.status_code,
                response_body=response_data,
            )

            # =================================================
            # SUCCESS
            # =================================================

            api_success = (
                response.status_code in (
                    200,
                    201,
                    202,
                )
                and response_data.get("success") is True
            )

            if api_success:

                # -------------------------------------------------
                # MARK SESSION DELETED
                # -------------------------------------------------

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

                session.save()

                return {
                    "success": True,
                    "status": "deleted",
                    "response": response_data,
                }

            # =================================================
            # API FAILURE
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
                    "contacting Telenity Delete API."
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
                    f"Delete API request failed: {exc}"
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