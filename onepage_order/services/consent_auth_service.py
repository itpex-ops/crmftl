import requests

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from ..models import ApiToken


class ConsentAuthService:

    @classmethod
    def get_consent_token(cls):
        """
        Get Telenity Consent API authentication token.

        Flow:
        1. Check existing valid token in ApiToken.
        2. If valid, return database token.
        3. Otherwise request a new token from Telenity.
        4. Save the new token and expiry in ApiToken.
        """

        # =========================================================
        # 1. CHECK EXISTING TOKEN
        # =========================================================

        token = (
            ApiToken.objects
            .filter(
                token_type="CONSENT",
                access_token__isnull=False,
            )
            .order_by("-updated_at")
            .first()
        )

        if token and token.expires_at:
            if token.expires_at > timezone.now():

                # Update last used time
                token.last_used = timezone.now()
                token.save(update_fields=["last_used"])

                return {
                    "success": True,
                    "token": token.access_token,
                    "source": "database",
                    "expires_at": token.expires_at.isoformat(),
                }

        # =========================================================
        # 2. API SETTINGS
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
            "Accept": "*/*",
        }

        # =========================================================
        # 4. PAYLOAD
        # =========================================================

        payload = {
            "grant_type": "client_credentials",
        }

        # =========================================================
        # 5. REQUEST TOKEN
        # =========================================================

        try:

            response = requests.post(
                url=url,
                headers=headers,
                data=payload,
                timeout=30,
            )

            # =====================================================
            # DEBUG
            # =====================================================

            print("\n")
            print("=" * 80)
            print("CONSENT AUTH RESPONSE")
            print("=" * 80)
            print("Status :", response.status_code)
            print("Response :", response.text)
            print("=" * 80)

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
            # 7. JSON RESPONSE
            # =====================================================

            try:
                data = response.json()

            except ValueError:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Consent Auth API returned "
                        "invalid JSON."
                    ),
                    "raw_response": response.text,
                }

            # =====================================================
            # 8. GET ACCESS TOKEN
            # =====================================================

            access_token = data.get("access_token")

            if not access_token:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": (
                        "Access token not returned "
                        "by Consent Auth API."
                    ),
                    "response": data,
                }

            # =====================================================
            # 9. TOKEN EXPIRY
            # =====================================================

            try:
                expires_in = int(
                    data.get(
                        "expires_in",
                        3600,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                expires_in = 3600

            expires_at = (
                timezone.now()
                + timedelta(seconds=expires_in)
            )

            # =====================================================
            # 10. SAVE TOKEN
            # =====================================================

            ApiToken.objects.update_or_create(

                token_type="CONSENT",

                defaults={
                    "access_token": access_token,
                    "response_json": data,
                    "expires_at": expires_at,
                    "last_used": timezone.now(),
                },
            )

            # =====================================================
            # 11. SUCCESS
            # =====================================================

            return {
                "success": True,
                "token": access_token,
                "token_type": data.get(
                    "token_type"
                ),
                "expires_in": expires_in,
                "expires_at": expires_at.isoformat(),
                "source": "Consent Auth API",
            }

        # =========================================================
        # 12. TIMEOUT
        # =========================================================

        except requests.exceptions.Timeout:

            return {
                "success": False,
                "message": (
                    "Consent authentication "
                    "request timed out."
                ),
            }

        # =========================================================
        # 13. CONNECTION ERROR
        # =========================================================

        except requests.exceptions.ConnectionError as e:

            return {
                "success": False,
                "message": (
                    "Unable to connect to "
                    "Telenity Consent Auth API."
                ),
                "error": str(e),
            }

        # =========================================================
        # 14. OTHER REQUEST ERROR
        # =========================================================

        except requests.exceptions.RequestException as e:

            return {
                "success": False,
                "message": (
                    "Consent authentication "
                    "request failed."
                ),
                "error": str(e),
            }

        # =========================================================
        # 15. UNEXPECTED ERROR
        # =========================================================

        except Exception as e:

            return {
                "success": False,
                "message": (
                    "Unexpected error while getting "
                    "Consent authentication token."
                ),
                "error": str(e),
            }