import requests

from django.conf import settings


class TrackingAuthService:

    @classmethod
    def get_tracking_token(cls):
        """
        Get the Telenity / SmartTrail Tracking API authentication token.

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

        # ---------------------------------------------------------
        # Validate configuration
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Headers
        # ---------------------------------------------------------

        headers = {
            "Authorization": (
                f"Basic {basic_token.strip()}"
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:

            # -----------------------------------------------------
            # Authentication API
            # -----------------------------------------------------

            response = requests.get(
                url=url,
                headers=headers,
                timeout=30,
            )

            # -----------------------------------------------------
            # HTTP error
            # -----------------------------------------------------

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        response.text.strip()
                        or "Tracking authentication failed."
                    ),
                }

            # -----------------------------------------------------
            # JSON response
            # -----------------------------------------------------

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

            # -----------------------------------------------------
            # Extract token
            # -----------------------------------------------------

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

            # -----------------------------------------------------
            # Success
            # -----------------------------------------------------

            return {
                "success": True,
                "status_code": response.status_code,
                "token": access_token,
                "response": data,
            }

        # ---------------------------------------------------------
        # Request errors
        # ---------------------------------------------------------

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Tracking authentication API "
                    "request timed out."
                ),
            }

        except requests.exceptions.ConnectionError as e:

            return {
                "success": False,
                "message": (
                    "Unable to connect to tracking "
                    "authentication API."
                ),
                "error": str(e),
            }

        except requests.exceptions.RequestException as e:

            return {
                "success": False,
                "message": (
                    "Tracking authentication API request failed."
                ),
                "error": str(e),
            }

        except Exception as e:

            return {
                "success": False,
                "message": (
                    "Unexpected error while getting "
                    "tracking authentication token."
                ),
                "error": str(e),
            }