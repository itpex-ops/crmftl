import logging
import requests

from datetime import datetime

from django.conf import settings
from django.utils import timezone

from onepage_order.models import (
    TrackingSession,
    LiveLocation,
    ApiLog,
)

from onepage_order.services.auth_service import (
    TrackingAuthService,
)


logger = logging.getLogger(__name__)


class LocationService:

    # =========================================================
    # MOBILE FORMAT
    # =========================================================

    @staticmethod
    def normalize_mobile(mobile):
        """
        Convert Indian mobile number to:

            91XXXXXXXXXX

        Examples:

            919876543210
            +919876543210
            09876543210
            9876543210

        Returns:
            str | None
        """

        mobile = str(mobile or "").strip()

        # Remove common formatting characters
        mobile = (
            mobile
            .replace("+", "")
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        # Remove 0091 prefix
        if mobile.startswith("0091"):
            mobile = mobile[4:]

        # Remove 91 prefix when 12 digits
        elif mobile.startswith("91") and len(mobile) == 12:
            mobile = mobile[2:]

        # Validate
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
                "location_available": False,
                "message": "Tracking session not found.",
            }

        # =====================================================
        # MOBILE
        # =====================================================

        mobile = cls.normalize_mobile(
            session.driver_mobile
        )

        if not mobile:

            logger.error(
                "LOCATION | Invalid mobile | session=%s mobile=%s",
                session.pk,
                session.driver_mobile,
            )

            return {
                "success": False,
                "location_available": False,
                "message": "Invalid driver mobile number.",
            }

        logger.info(
            "LOCATION FETCH START | "
            "session=%s trip=%s mobile=%s "
            "entity=%s status=%s",
            session.pk,
            session.order.trip_number if session.order else None,
            mobile,
            session.entity_id,
            session.status,
        )

        # =====================================================
        # GET TRACKING TOKEN
        # =====================================================

        auth = TrackingAuthService.get_tracking_token()

        if not auth.get("success"):

            logger.error(
                "LOCATION AUTH FAILED | session=%s | auth=%s",
                session.pk,
                auth,
            )

            return {
                "success": False,
                "location_available": False,
                "message": auth.get(
                    "message",
                    "Unable to get tracking token.",
                ),
                "auth_response": auth,
            }

        token = auth.get("token")

        if not token:

            logger.error(
                "LOCATION AUTH TOKEN MISSING | session=%s",
                session.pk,
            )

            return {
                "success": False,
                "location_available": False,
                "message": (
                    "Tracking authentication succeeded "
                    "but token was not returned."
                ),
            }

        # =====================================================
        # LOCATION API
        # =====================================================

        base_url = getattr(
            settings,
            "TELENITY_LOCATION_API",
            "",
        )

        if not base_url:

            logger.error(
                "TELENITY_LOCATION_API NOT CONFIGURED"
            )

            return {
                "success": False,
                "location_available": False,
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

        logger.info(
            "LOCATION API REQUEST | "
            "session=%s trip=%s url=%s",
            session.pk,
            session.order.trip_number if session.order else None,
            url,
        )

        try:

            # =================================================
            # CALL LOCATION API
            # =================================================

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30,
            )

            # =================================================
            # PARSE RESPONSE
            # =================================================

            try:

                response_data = response.json()

            except ValueError:

                response_data = {
                    "raw_response": response.text
                }

            logger.info(
                "LOCATION API RESPONSE | "
                "session=%s status_code=%s",
                session.pk,
                response.status_code,
            )

            # =================================================
            # API LOG
            # =================================================

            try:

                ApiLog.objects.create(
                    api_name="Location API",
                    request_url=url,
                    request_method="GET",
                    request_headers={
                        "Token": "********",
                        "Accept": "application/json",
                    },
                    request_body=None,
                    response_code=response.status_code,
                    response_body=response_data,
                )

            except Exception:

                logger.exception(
                    "LOCATION API LOG SAVE FAILED | "
                    "session=%s",
                    session.pk,
                )

            # =================================================
            # HTTP ERROR
            # =================================================

            if response.status_code != 200:

                session.location_status = "error"

                session.save(
                    update_fields=[
                        "location_status",
                    ]
                )

                logger.error(
                    "LOCATION API HTTP ERROR | "
                    "session=%s status=%s response=%s",
                    session.pk,
                    response.status_code,
                    response_data,
                )

                return {
                    "success": False,
                    "location_available": False,
                    "status_code": response.status_code,
                    "message": (
                        "Location API request failed."
                    ),
                    "response": response_data,
                }

            # =================================================
            # TERMINAL LOCATION
            # =================================================

            terminal_locations = (
                response_data.get(
                    "terminalLocation"
                )
                or []
            )

            if not terminal_locations:

                logger.warning(
                    "LOCATION NOT AVAILABLE | "
                    "session=%s trip=%s",
                    session.pk,
                    session.order.trip_number
                    if session.order
                    else None,
                )

                # Do NOT delete previous location.
                # Vehicle may simply not have a fresh
                # location yet.

                session.location_status = (
                    "waiting_location"
                )

                if session.consent_received:

                    session.status = (
                        "waiting_location"
                    )

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

            # =================================================
            # FIRST TERMINAL
            # =================================================

            terminal = terminal_locations[0]

            # =================================================
            # ENTITY ID
            # =================================================

            entity_id = terminal.get(
                "entityId"
            )

            # =================================================
            # LOCATION STATUS
            # =================================================

            api_location_status = terminal.get(
                "status"
            )

            # =================================================
            # CURRENT LOCATION OBJECT
            # =================================================

            current_location = terminal.get(
                "currentLocation"
            )

            if not isinstance(
                current_location,
                dict,
            ):

                logger.warning(
                    "CURRENT LOCATION MISSING | "
                    "session=%s entity=%s",
                    session.pk,
                    entity_id,
                )

                update_fields = []

                if entity_id:

                    session.entity_id = entity_id

                    update_fields.append(
                        "entity_id"
                    )

                if api_location_status:

                    session.location_status = str(
                        api_location_status
                    )

                    update_fields.append(
                        "location_status"
                    )

                if session.consent_received:

                    session.status = (
                        "waiting_location"
                    )

                    update_fields.append(
                        "status"
                    )

                if update_fields:

                    session.save(
                        update_fields=update_fields
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

            # =================================================
            # EXTRACT LOCATION
            # =================================================

            latitude = current_location.get(
                "latitude"
            )

            longitude = current_location.get(
                "longitude"
            )

            address = (
                current_location.get(
                    "detailedAddress"
                )
                or current_location.get(
                    "address"
                )
                or ""
            )

            accuracy = current_location.get(
                "accuracy"
            )

            # -------------------------------------------------
            # IMPORTANT:
            # Telenity may not return accuracy.
            # LiveLocation.accuracy has default=0 but the
            # field itself is not nullable.
            # -------------------------------------------------

            if accuracy is None:

                accuracy = 0

            # Convert numeric accuracy safely

            try:

                accuracy = float(
                    accuracy
                )

            except (
                TypeError,
                ValueError,
            ):

                accuracy = 0

            location_name = (
                current_location.get(
                    "locationName"
                )
                or current_location.get(
                    "name"
                )
                or ""
            )

            location_timestamp = (
                current_location.get(
                    "timestamp"
                )
            )

            logger.info(
                "LOCATION EXTRACTED | "
                "session=%s lat=%s lng=%s "
                "location=%s accuracy=%s",
                session.pk,
                latitude,
                longitude,
                location_name,
                accuracy,
            )

            # =================================================
            # VALIDATE COORDINATES
            # =================================================

            if (
                latitude is None
                or longitude is None
            ):

                logger.warning(
                    "INVALID COORDINATES | "
                    "session=%s lat=%s lng=%s",
                    session.pk,
                    latitude,
                    longitude,
                )

                update_fields = []

                if entity_id:

                    session.entity_id = entity_id

                    update_fields.append(
                        "entity_id"
                    )

                if api_location_status:

                    session.location_status = str(
                        api_location_status
                    )

                    update_fields.append(
                        "location_status"
                    )

                if session.consent_received:

                    session.status = (
                        "waiting_location"
                    )

                    update_fields.append(
                        "status"
                    )

                if update_fields:

                    session.save(
                        update_fields=update_fields
                    )

                return {
                    "success": True,
                    "location_available": False,
                    "status": "waiting_location",
                    "message": (
                        "Location API returned "
                        "currentLocation without "
                        "latitude/longitude."
                    ),
                    "response": response_data,
                }

            # =================================================
            # TIMESTAMP
            # =================================================

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

                    if (
                        parsed_timestamp.tzinfo
                        is None
                    ):

                        parsed_timestamp = (
                            timezone.make_aware(
                                parsed_timestamp
                            )
                        )

                    received_at = (
                        parsed_timestamp
                    )

                except (
                    ValueError,
                    TypeError,
                ):

                    logger.warning(
                        "INVALID LOCATION TIMESTAMP | "
                        "session=%s timestamp=%s",
                        session.pk,
                        location_timestamp,
                    )

                    received_at = (
                        timezone.now()
                    )

            # =================================================
            # UPDATE TRACKING SESSION
            # =================================================

            session.latitude = latitude

            session.longitude = longitude

            session.last_location = (
                address
                or location_name
            )

            session.last_updated = (
                received_at
            )

            session.location_status = (
                "Retrieved"
            )

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

                session.entity_id = entity_id

                update_fields.append(
                    "entity_id"
                )

            session.save(
                update_fields=update_fields
            )

            logger.info(
                "TRACKING SESSION UPDATED | "
                "session=%s trip=%s "
                "lat=%s lng=%s",
                session.pk,
                session.order.trip_number
                if session.order
                else None,
                latitude,
                longitude,
            )

            # =================================================
            # SAVE LOCATION HISTORY
            # =================================================

            try:

                live_location = (
                    LiveLocation.objects.create(
                        session=session,
                        tracked=True,
                        location_status="active",
                        address=address or "",
                        latitude=latitude,
                        longitude=longitude,
                        accuracy=accuracy,
                        location_name=(
                            location_name or ""
                        ),
                        received_at=received_at,
                    )
                )

            except Exception as exc:

                logger.exception(
                    "LIVE LOCATION HISTORY SAVE FAILED | "
                    "session=%s trip=%s error=%s",
                    session.pk,
                    session.order.trip_number
                    if session.order
                    else None,
                    exc,
                )

                return {
                    "success": False,
                    "location_available": True,
                    "message": (
                        "Current location was received, "
                        "but location history could "
                        "not be saved."
                    ),
                    "error": str(exc),
                    "latitude": latitude,
                    "longitude": longitude,
                }

            logger.info(
                "LIVE LOCATION HISTORY SAVED | "
                "session=%s trip=%s "
                "location_id=%s "
                "lat=%s lng=%s received_at=%s",
                session.pk,
                session.order.trip_number
                if session.order
                else None,
                live_location.pk,
                latitude,
                longitude,
                received_at,
            )

            # =================================================
            # SUCCESS
            # =================================================

            return {
                "success": True,
                "location_available": True,
                "status": "active",
                "message": (
                    "Vehicle location received "
                    "successfully."
                ),
                "latitude": latitude,
                "longitude": longitude,
                "address": address,
                "accuracy": accuracy,
                "location_name": location_name,
                "received_at": received_at,
                "live_location_id": (
                    live_location.pk
                ),
                "response": response_data,
            }

        # =====================================================
        # TIMEOUT
        # =====================================================

        except requests.exceptions.Timeout:

            logger.exception(
                "LOCATION API TIMEOUT | session=%s",
                session.pk,
            )

            return {
                "success": False,
                "location_available": False,
                "message": (
                    "Location API request timed out."
                ),
            }

        # =====================================================
        # CONNECTION ERROR
        # =====================================================

        except requests.exceptions.ConnectionError as exc:

            logger.exception(
                "LOCATION API CONNECTION ERROR | "
                "session=%s error=%s",
                session.pk,
                exc,
            )

            return {
                "success": False,
                "location_available": False,
                "message": (
                    "Unable to connect to "
                    "Telenity Location API."
                ),
                "error": str(exc),
            }

        # =====================================================
        # REQUEST ERROR
        # =====================================================

        except requests.exceptions.RequestException as exc:

            logger.exception(
                "LOCATION API REQUEST ERROR | "
                "session=%s error=%s",
                session.pk,
                exc,
            )

            return {
                "success": False,
                "location_available": False,
                "message": (
                    f"Location API request failed: {exc}"
                ),
            }

        # =====================================================
        # UNEXPECTED ERROR
        # =====================================================

        except Exception as exc:

            logger.exception(
                "LOCATION SERVICE UNEXPECTED ERROR | "
                "session=%s error=%s",
                session.pk,
                exc,
            )

            return {
                "success": False,
                "location_available": False,
                "message": (
                    "Unexpected error while retrieving "
                    "vehicle location."
                ),
                "error": str(exc),
            }

    # =========================================================
    # GET LOCATION
    # =========================================================

    @classmethod
    def get_location(cls, mobile):

        normalized_mobile = (
            cls.normalize_mobile(mobile)
        )

        if not normalized_mobile:

            return {
                "success": False,
                "message": (
                    "Invalid driver mobile number."
                ),
            }

        # =====================================================
        # GET TRACKING TOKEN
        # =====================================================

        auth = (
            TrackingAuthService
            .get_tracking_token()
        )

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

        # =====================================================
        # LOCATION API
        # =====================================================

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
                "success": (
                    response.status_code == 200
                ),
                "status_code": (
                    response.status_code
                ),
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

            logger.exception(
                "GET LOCATION UNEXPECTED ERROR | "
                "mobile=%s",
                normalized_mobile,
            )

            return {
                "success": False,
                "message": str(exc),
            }