import requests

from django.conf import settings


class TrackingAuthService:

    @classmethod
    def get_tracking_token(cls):
        """
        Get Telenity / SmartTrail Tracking API authentication token.

        Returns:

            {
                "success": True,
                "token": "...",
                "status_code": 200,
                "response": {...}
            }

        or:

            {
                "success": False,
                "status_code": ...,
                "message": "..."
            }
        """

        # =========================================================
        # SETTINGS
        # =========================================================

        url = getattr(
            settings,
            "TELENITY_TRACKING_AUTH_API",
            "",
        )

        basic_token = getattr(
            settings,
            "TELENITY_TRACKING_BASIC_TOKEN",
            "",
        )

        # =========================================================
        # VALIDATE SETTINGS
        # =========================================================

        if not url:

            return {
                "success": False,
                "message": (
                    "TELENITY_TRACKING_AUTH_API "
                    "is not configured."
                ),
            }

        if not basic_token:

            return {
                "success": False,
                "message": (
                    "TELENITY_TRACKING_BASIC_TOKEN "
                    "is not configured."
                ),
            }

        # =========================================================
        # HEADERS
        # =========================================================

        headers = {
            "Authorization": (
                f"Basic {basic_token.strip()}"
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:

            # =====================================================
            # AUTHENTICATION API
            # =====================================================

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30,
            )

            # =====================================================
            # HTTP ERROR
            # =====================================================

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        response.text.strip()
                        or "Tracking authentication failed."
                    ),
                }

            # =====================================================
            # JSON RESPONSE
            # =====================================================

            try:

                data = response.json()

            except ValueError:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Tracking authentication API "
                        "returned invalid JSON."
                    ),
                    "raw_response": response.text,
                }

            # =====================================================
            # GET TOKEN
            # =====================================================

            access_token = data.get("token")

            if not access_token:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Token not found in tracking "
                        "authentication API response."
                    ),
                    "response": data,
                }

            # =====================================================
            # SUCCESS
            # =====================================================

            return {
                "success": True,
                "status_code": response.status_code,
                "token": access_token,
                "response": data,
            }

        # =========================================================
        # TIMEOUT
        # =========================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Tracking authentication API "
                    "request timed out."
                ),
            }

        # =========================================================
        # CONNECTION ERROR
        # =========================================================

        except requests.exceptions.ConnectionError as exc:

            return {
                "success": False,
                "message": (
                    "Unable to connect to tracking "
                    "authentication API."
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
                    "Tracking authentication API "
                    "request failed."
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
                    "Unexpected error while getting "
                    "tracking authentication token."
                ),
                "error": str(exc),
            }