import requests

from datetime import datetime

from django.conf import settings
from django.utils import timezone

from onepage_order.models import TrackingSession, LiveLocation, ApiLog
from onepage_order.services.auth_service import TrackingAuthService


class LocationService:

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
    # FETCH LOCATION
    # =========================================================

    @classmethod
    def fetch_location(cls, session):

        if not session:

            return {
                "success": False,
                "message": "Tracking session not found.",
            }

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
                    "Unable to get tracking token.",
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
        # Location API
        # ---------------------------------------------------------

        base_url = getattr(
            settings,
            "TELENITY_LOCATION_API",
            "",
        )

        if not base_url:

            return {
                "success": False,
                "message": (
                    "TELENITY_LOCATION_API "
                    "is not configured."
                ),
            }

        url = (
            f"{base_url.rstrip('/')}"
            f"/{mobile}"
            f"?lastResult=True"
        )

        headers = {
            "Token": token,
            "Accept": "application/json",
        }

        try:

            # =====================================================
            # CALL LOCATION API
            # =====================================================

            response = requests.get(
                url=url,
                headers=headers,
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
                    api_name="Location API",
                    request_url=url,
                    request_method="GET",
                    request_headers={
                        "Token": "********",
                    },
                    request_body=None,
                    response_code=response.status_code,
                    response_body=response_data,
                )

            except Exception:
                pass

            # =====================================================
            # HTTP ERROR
            # =====================================================

            if response.status_code != 200:

                session.location_status = "error"

                session.save(
                    update_fields=[
                        "location_status",
                    ]
                )

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Location API request failed."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # TERMINAL LOCATION
            # =====================================================

            terminal_locations = (
                response_data.get("terminalLocation")
                or []
            )

            if not terminal_locations:

                # Do NOT delete previous location.
                # Vehicle may simply not have a fresh
                # location yet.

                session.location_status = (
                    "waiting_location"
                )

                if session.consent_received:

                    session.status = "waiting_location"

                session.save(
                    update_fields=[
                        "location_status",
                        "status",
                    ]
                )

                return {
                    "success": True,
                    "location_available": False,
                    "status": "waiting_location",
                    "message": (
                        "No current vehicle location "
                        "is available."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # FIRST TERMINAL LOCATION
            # =====================================================

            terminal = terminal_locations[0]

            # -----------------------------------------------------
            # Entity ID
            # -----------------------------------------------------

            entity_id = terminal.get("entityId")

            if entity_id:
                session.entity_id = entity_id

            # -----------------------------------------------------
            # Location status
            # -----------------------------------------------------

            api_location_status = terminal.get(
                "status"
            )

            if api_location_status:
                session.location_status = (
                    str(api_location_status)
                )

            # -----------------------------------------------------
            # Current location object
            # -----------------------------------------------------

            current_location = (
                terminal.get("currentLocation")
            )

            if not isinstance(
                current_location,
                dict,
            ):

                if session.consent_received:

                    session.status = "waiting_location"

                session.save(
                    update_fields=[
                        "entity_id",
                        "location_status",
                        "status",
                    ]
                )

                return {
                    "success": True,
                    "location_available": False,
                    "status": "waiting_location",
                    "message": (
                        "Terminal found, but current "
                        "location is not available."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # EXTRACT LOCATION
            # =====================================================

            latitude = current_location.get(
                "latitude"
            )

            longitude = current_location.get(
                "longitude"
            )

            address = current_location.get(
                "detailedAddress"
            )

            accuracy = current_location.get(
                "accuracy"
            )

            location_name = (
                current_location.get("locationName")
                or current_location.get("name")
                or ""
            )

            location_timestamp = (
                current_location.get("timestamp")
            )

            # -----------------------------------------------------
            # Validate coordinates
            # -----------------------------------------------------

            if latitude is None or longitude is None:

                if session.consent_received:

                    session.status = "waiting_location"

                session.save(
                    update_fields=[
                        "entity_id",
                        "location_status",
                        "status",
                    ]
                )

                return {
                    "success": True,
                    "location_available": False,
                    "status": "waiting_location",
                    "message": (
                        "Location API returned currentLocation "
                        "without latitude/longitude."
                    ),
                    "response": response_data,
                }

            # =====================================================
            # TIMESTAMP
            # =====================================================

            received_at = timezone.now()

            if location_timestamp:

                try:

                    timestamp_string = str(
                        location_timestamp
                    )

                    parsed_timestamp = (
                        datetime.fromisoformat(
                            timestamp_string.replace(
                                "Z",
                                "+00:00",
                            )
                        )
                    )

                    if parsed_timestamp.tzinfo is None:

                        parsed_timestamp = (
                            timezone.make_aware(
                                parsed_timestamp
                            )
                        )

                    received_at = parsed_timestamp

                except (
                    ValueError,
                    TypeError,
                ):

                    received_at = timezone.now()

            # =====================================================
            # UPDATE TRACKING SESSION
            # =====================================================

            session.latitude = latitude
            session.longitude = longitude
            session.last_location = address or location_name
            session.last_updated = received_at
            session.location_status = "active"
            session.tracking_enabled = True
            session.status = "active"

            update_fields = [
                "latitude",
                "longitude",
                "last_location",
                "last_updated",
                "location_status",
                "tracking_enabled",
                "status",
            ]

            if entity_id:
                update_fields.append("entity_id")

            session.save(
                update_fields=update_fields
            )

            # =====================================================
            # SAVE LIVE LOCATION HISTORY
            # =====================================================

            live_location = LiveLocation.objects.create(
                session=session,
                tracked=True,
                location_status="active",
                address=address or "",
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                location_name=location_name,
                received_at=received_at,
            )

            # =====================================================
            # SUCCESS
            # =====================================================

            return {
                "success": True,
                "location_available": True,
                "status": "active",
                "message": (
                    "Vehicle location received successfully."
                ),
                "latitude": latitude,
                "longitude": longitude,
                "address": address,
                "accuracy": accuracy,
                "location_name": location_name,
                "received_at": received_at,
                "live_location_id": live_location.pk,
                "response": response_data,
            }

        # =========================================================
        # TIMEOUT
        # =========================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Location API request timed out."
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
                    "Telenity Location API."
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
                    f"Location API request failed: {exc}"
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

    # =========================================================
    # GET LOCATION
    # =========================================================

    @classmethod
    def get_location(cls, mobile):

        normalized_mobile = cls.normalize_mobile(
            mobile
        )

        if not normalized_mobile:

            return {
                "success": False,
                "message": (
                    "Invalid driver mobile number."
                ),
            }

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):
            return auth

        token = auth.get("token")

        if not token:

            return {
                "success": False,
                "message": (
                    "Tracking token not available."
                ),
            }

        base_url = getattr(
            settings,
            "TELENITY_LOCATION_API",
            "",
        )

        if not base_url:

            return {
                "success": False,
                "message": (
                    "TELENITY_LOCATION_API "
                    "is not configured."
                ),
            }

        url = (
            f"{base_url.rstrip('/')}"
            f"/{normalized_mobile}"
            f"?lastResult=True"
        )

        headers = {
            "Token": token,
            "Accept": "application/json",
        }

        try:

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30,
            )

            try:

                data = response.json()

            except ValueError:

                data = {
                    "raw_response": response.text
                }

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": data,
            }

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Location API request timed out."
                ),
            }

        except requests.exceptions.ConnectionError as exc:

            return {
                "success": False,
                "message": (
                    "Unable to connect to "
                    "Telenity Location API."
                ),
                "error": str(exc),
            }

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": (
                    f"Location API request failed: {exc}"
                ),
            }

        except Exception as exc:

            return {
                "success": False,
                "message": str(exc),
            }