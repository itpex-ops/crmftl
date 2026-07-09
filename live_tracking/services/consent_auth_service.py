import requests

from django.conf import settings


class ConsentAuthService:

    @classmethod
    def get_consent_token(cls):

        url = (
            "https://india-agw.telenity.com/oauth/token"
            "?grant_type=client_credentials"
        )

        headers = {
            "Authorization": f"Basic {settings.TELENITY_BASIC_TOKEN.strip()}",
            "Accept": "*/*"
        }

        response = requests.post(
            url,
            headers=headers,
            timeout=30
        )

        print("Consent Status :", response.status_code)
        print("Consent Response :", response.text)

        return response