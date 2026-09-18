import requests

from django.conf import settings
from django.utils.dateparse import parse_datetime

from .auth_service import TrackingAuthService

from ..models import ApiLog, LiveLocation


class LocationService:

    # =========================================================
    # MOBILE NORMALIZATION
    # =========================================================

    @staticmethod
    def normalize_mobile(mobile):
        """
        Convert Indian mobile number into:

            91XXXXXXXXXX

        Accepted:

            9876543210
            919876543210
            +919876543210
            00919876543210
        """

        mobile = str(mobile or "").strip()

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
            return None

        return "91" + mobile

    # =========================================================
    # FETCH LOCATION
    # =========================================================

    @classmethod
    def fetch_location(cls, session):

        if not session:
            return {
                "success": False,
                "message": "Tracking session not found."
            }

        # -----------------------------------------------------
        # GET LOCATION
        # -----------------------------------------------------

        result = cls.get_location(
            session.driver_mobile
        )

        if not result.get("success"):
            return result

        response = result.get("response") or {}

        mobile = cls.normalize_mobile(
            session.driver_mobile
        )

        # -----------------------------------------------------
        # API LOG
        # -----------------------------------------------------

        ApiLog.objects.create(
            api_name="Location API",
            request_url=(
                f"{settings.TELENITY_LOCATION_API}"
                f"/{mobile}?lastResult=True"
            ),
            request_method="GET",
            request_headers={
                "Token": "********",
                "Content-Type": "application/json",
            },
            request_body=None,
            response_code=result.get("status_code"),
            response_body=response,
        )

        # -----------------------------------------------------
        # TERMINAL LOCATION
        # -----------------------------------------------------

        terminals = response.get(
            "terminalLocation",
            []
        )

        if not terminals:

            # No location returned.
            #
            # Do NOT mark the vehicle active merely because
            # consent has been received.

            if session.consent_received:
                session.status = "waiting_location"

            session.tracking_enabled = (
                session.tracking_enabled
            )

            session.save(
                update_fields=[
                    "status",
                    "tracking_enabled",
                ]
            )

            return {
                "success": False,
                "message": "Location not available.",
                "response": response,
            }

        # -----------------------------------------------------
        # FIRST TERMINAL
        # -----------------------------------------------------

        terminal = terminals[0]

        print()
        print("=" * 80)
        print("TERMINAL DATA")
        print("=" * 80)
        print(
            "Entity ID       :",
            terminal.get("entityId")
        )
        print(
            "Tracked         :",
            terminal.get("tracked")
        )
        print(
            "Location Status :",
            terminal.get("locationRetrievalStatus")
        )
        print(
            "Result Status   :",
            terminal.get("locationResultStatus")
        )
        print(
            "Current Location:",
            terminal.get("currentLocation")
        )
        print("=" * 80)

        # -----------------------------------------------------
        # SESSION DATA
        # -----------------------------------------------------

        session.entity_id = (
            terminal.get("entityId")
            or session.entity_id
        )

        session.location_status = (
            terminal.get(
                "locationRetrievalStatus"
            )
        )

        session.tracking_enabled = bool(
            terminal.get("tracked", False)
        )

        current = terminal.get(
            "currentLocation"
        )

        # =====================================================
        # LOCATION AVAILABLE
        # =====================================================

        if current:

            latitude = current.get(
                "latitude"
            )

            longitude = current.get(
                "longitude"
            )

            detailed_address = current.get(
                "detailedAddress",
                ""
            )

            accuracy = current.get(
                "accuracy",
                0
            )

            # -------------------------------------------------
            # UPDATE SESSION LOCATION
            # -------------------------------------------------

            session.latitude = latitude
            session.longitude = longitude

            session.last_location = (
                detailed_address
            )

            timestamp = current.get(
                "timestamp"
            )

            parsed_datetime = None

            if timestamp:

                try:

                    timestamp_value = str(
                        timestamp
                    ).strip()

                    # Handle timestamps containing
                    # a space between date/time.

                    if " " in timestamp_value:
                        timestamp_value = (
                            timestamp_value.replace(
                                " ",
                                "T",
                                1
                            )
                        )

                    parsed_datetime = parse_datetime(
                        timestamp_value
                    )

                except Exception:
                    parsed_datetime = None

            if parsed_datetime:

                session.last_updated = (
                    parsed_datetime
                )

            else:

                session.last_updated = (
                    session.last_updated
                )

            # -------------------------------------------------
            # ACTIVE
            # -------------------------------------------------

            session.status = "active"

            session.save()

            # -------------------------------------------------
            # SAVE LIVE LOCATION
            # -------------------------------------------------

            LiveLocation.objects.create(
                session=session,
                tracked=bool(
                    terminal.get(
                        "tracked",
                        True
                    )
                ),
                location_status=terminal.get(
                    "locationRetrievalStatus"
                ),
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy or 0,
                address=detailed_address,
                location_name=detailed_address,
                received_at=(
                    parsed_datetime
                    or session.last_updated
                ),
            )

        # =====================================================
        # LOCATION NOT AVAILABLE
        # =====================================================

        else:

            print(
                "Telenity returned no currentLocation."
            )

            # Consent is already approved and tracking
            # has been started, but location has not arrived.

            if session.consent_received:

                session.status = (
                    "waiting_location"
                )

            # IMPORTANT:
            # Do not clear the previous location.
            #
            # Keeping the previous location prevents the UI
            # from suddenly becoming blank when Telenity
            # temporarily doesn't return currentLocation.
            #
            # If you intentionally want to clear stale
            # locations, remove the previous values here.

            session.save()

        # -----------------------------------------------------
        # DEBUG
        # -----------------------------------------------------

        print()
        print("=" * 80)
        print("SESSION SAVED")
        print("=" * 80)
        print(
            "Status           :",
            session.status
        )
        print(
            "Tracking Enabled :",
            session.tracking_enabled
        )
        print(
            "Latitude         :",
            session.latitude
        )
        print(
            "Longitude        :",
            session.longitude
        )
        print(
            "Last Location    :",
            session.last_location
        )
        print(
            "Location Status  :",
            session.location_status
        )
        print("=" * 80)

        return {
            "success": True,
            "response": response,
            "session": session,
        }

    # =========================================================
    # GET LOCATION FROM TELENITY
    # =========================================================

    @classmethod
    def get_location(cls, driver_mobile):

        # -----------------------------------------------------
        # AUTHENTICATION
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
        # MOBILE
        # -----------------------------------------------------

        driver_mobile = cls.normalize_mobile(
            driver_mobile
        )

        if not driver_mobile:

            return {
                "success": False,
                "message": "Invalid Driver Mobile Number."
            }

        # -----------------------------------------------------
        # URL
        # -----------------------------------------------------

        base_url = getattr(
            settings,
            "TELENITY_LOCATION_API",
            ""
        )

        if not base_url:

            return {
                "success": False,
                "message": "TELENITY_LOCATION_API is not configured."
            }

        url = (
            f"{base_url}/{driver_mobile}"
            f"?lastResult=True"
        )

        # -----------------------------------------------------
        # HEADERS
        # -----------------------------------------------------

        headers = {
            "Token": token,
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        masked_token = "********"

        if len(token) > 12:

            masked_token = (
                token[:8]
                + "********"
            )

        # -----------------------------------------------------
        # REQUEST DEBUG
        # -----------------------------------------------------

        print()
        print("=" * 80)
        print("LOCATION API REQUEST")
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
        print("=" * 80)

        try:

            # -------------------------------------------------
            # REQUEST
            # -------------------------------------------------

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

            print()
            print("=" * 80)
            print("LOCATION API RESPONSE")
            print("=" * 80)
            print("Status :", response.status_code)
            print("Response :", response_data)
            print("=" * 80)

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response_data,
            }

        # =====================================================
        # TIMEOUT
        # =====================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Connection timeout while "
                    "contacting Telenity Location API."
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
                    f"Location API request failed: {exc}"
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