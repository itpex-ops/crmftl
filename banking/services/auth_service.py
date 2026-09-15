import requests

from django.conf import settings


class AxisAuthService:

    @classmethod
    def get_access_token(cls):
        """
        Returns Axis Bank Access Token
        """

        url = ""

        headers = {}

        payload = {}

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            return response.json()

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }
