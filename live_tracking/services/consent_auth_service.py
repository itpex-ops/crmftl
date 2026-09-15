import requests

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from live_tracking.models import ApiToken


class ConsentAuthService:

    @classmethod
    def get_consent_token(cls):

        # -------------------------------------------------
        # CHECK EXISTING TOKEN
        # -------------------------------------------------

        token = ApiToken.objects.filter(
            token_type="CONSENT"
        ).first()

        if token and token.expires_at > timezone.now():

            return {
                "success": True,
                "token": token.access_token,
                "source": "database"
            }

        # -------------------------------------------------
        # API DETAILS
        # -------------------------------------------------

        url = settings.TELENITY_CONSENT_AUTH_API

        headers = {
            "Authorization": f"Basic {settings.TELENITY_CONSENT_BASIC_TOKEN.strip()}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*"
        }

        payload = {
            "grant_type": "client_credentials"
        }

        response = requests.post(
            settings.TELENITY_CONSENT_AUTH_API,
            headers=headers,
            data=payload,   # IMPORTANT: data=, not json=
            timeout=30
        )

        try:

            response = requests.post(
                url=url,
                headers=headers,
                data=payload,          # IMPORTANT: use data= not json=
                timeout=30
            )

            print("\n")
            print("=" * 80)
            print("CONSENT AUTH RESPONSE")
            print("=" * 80)
            print("Status :", response.status_code)
            print("Response :", response.text)
            print("=" * 80)

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": response.text
                }

            data = response.json()

            access_token = data.get("access_token")

            if not access_token:

                return {
                    "success": False,
                    "message": "Access token not returned."
                }

            expires_in = int(data.get("expires_in", 3600))

            ApiToken.objects.update_or_create(

                token_type="CONSENT",

                defaults={

                    "access_token": access_token,

                    "expires_at": timezone.now() + timedelta(seconds=expires_in)

                }

            )

            return {

                "success": True,

                "token": access_token,

                "token_type": data.get("token_type"),

                "expires_in": expires_in,

                "source": "Consent Auth API"

            }

        except requests.exceptions.Timeout:

            return {

                "success": False,

                "message": "Connection Timeout."

            }

        except requests.exceptions.ConnectionError:

            return {

                "success": False,

                "message": "Unable to connect to Telenity Server."

            }

        except Exception as e:

            return {

                "success": False,

                "message": str(e)

            }