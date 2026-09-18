import requests

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from onepage_order.models import ApiToken


class ConsentAuthService:

    @classmethod
    def get_consent_token(cls):
        """
        Get Telenity Consent API access token.

        First checks ApiToken table for an existing valid token.
        If no valid token exists, requests a new token from the
        Consent Authentication API and stores it in ApiToken.

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
                "message": "..."
            }
        """

        # =========================================================
        # 1. CHECK DATABASE TOKEN
        # =========================================================

        existing_token = (
            ApiToken.objects
            .filter(
                token_type="CONSENT",
                expires_at__gt=timezone.now(),
            )
            .order_by("-updated_at")
            .first()
        )

        if existing_token:

            existing_token.last_used = timezone.now()
            existing_token.save(
                update_fields=["last_used"]
            )

            return {
                "success": True,
                "token": existing_token.access_token,
                "status_code": 200,
                "response": existing_token.response_json,
                "from_cache": True,
            }

        # =========================================================
        # 2. READ SETTINGS
        # =========================================================

        url = getattr(
            settings,
            "TELENITY_CONSENT_AUTH_API",
            "",
        )

        basic_token = getattr(
            settings,
            "TELENITY_CONSENT_BASIC_TOKEN",
            "",
        )

        if not url:

            return {
                "success": False,
                "message": (
                    "TELENITY_CONSENT_AUTH_API "
                    "is not configured."
                ),
            }

        if not basic_token:

            return {
                "success": False,
                "message": (
                    "TELENITY_CONSENT_BASIC_TOKEN "
                    "is not configured."
                ),
            }

        # =========================================================
        # 3. HEADERS
        # =========================================================

        headers = {
            "Authorization": (
                f"Basic {basic_token.strip()}"
            ),
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
            "Accept": "application/json",
        }

        # =========================================================
        # 4. REQUEST PAYLOAD
        # =========================================================

        payload = {
            "grant_type": "client_credentials",
        }

        try:

            # =====================================================
            # 5. AUTHENTICATION REQUEST
            # =====================================================

            response = requests.post(
                url=url,
                headers=headers,
                data=payload,
                timeout=30,
            )

            # =====================================================
            # 6. HTTP ERROR
            # =====================================================

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        response.text.strip()
                        or "Consent authentication failed."
                    ),
                }

            # =====================================================
            # 7. PARSE JSON
            # =====================================================

            try:

                data = response.json()

            except ValueError:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Consent authentication API "
                        "returned invalid JSON."
                    ),
                    "raw_response": response.text,
                }

            # =====================================================
            # 8. EXTRACT ACCESS TOKEN
            # =====================================================

            access_token = data.get("access_token")

            if not access_token:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "access_token not found in consent "
                        "authentication response."
                    ),
                    "response": data,
                }

            # =====================================================
            # 9. TOKEN EXPIRY
            # =====================================================

            expires_in = data.get("expires_in")

            try:

                expires_in = int(expires_in)

            except (TypeError, ValueError):

                # Default: 1 hour
                expires_in = 3600

            # Small safety buffer so we don't use a token
            # right at the exact expiry time.
            expiry_seconds = max(
                expires_in - 60,
                60,
            )

            expires_at = (
                timezone.now()
                + timedelta(seconds=expiry_seconds)
            )

            # =====================================================
            # 10. SAVE TOKEN
            # =====================================================

            token_object, created = (
                ApiToken.objects.update_or_create(
                    token_type="CONSENT",
                    defaults={
                        "access_token": access_token,
                        "response_json": data,
                        "last_used": timezone.now(),
                        "expires_at": expires_at,
                    },
                )
            )

            # =====================================================
            # 11. SUCCESS
            # =====================================================

            return {
                "success": True,
                "token": token_object.access_token,
                "status_code": response.status_code,
                "response": data,
                "from_cache": False,
            }

        # =========================================================
        # 12. TIMEOUT
        # =========================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Consent authentication API "
                    "request timed out."
                ),
            }

        # =========================================================
        # 13. CONNECTION ERROR
        # =========================================================

        except requests.exceptions.ConnectionError as exc:

            return {
                "success": False,
                "message": (
                    "Unable to connect to consent "
                    "authentication API."
                ),
                "error": str(exc),
            }

        # =========================================================
        # 14. REQUEST ERROR
        # =========================================================

        except requests.exceptions.RequestException as exc:

            return {
                "success": False,
                "message": (
                    "Consent authentication API "
                    "request failed."
                ),
                "error": str(exc),
            }

        # =========================================================
        # 15. UNEXPECTED ERROR
        # =========================================================

        except Exception as exc:

            return {
                "success": False,
                "message": (
                    "Unexpected error while getting "
                    "consent authentication token."
                ),
                "error": str(exc),
            }