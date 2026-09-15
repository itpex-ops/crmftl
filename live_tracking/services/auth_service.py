import requests
from django.conf import settings
class TrackingAuthService:
    @classmethod
    def get_tracking_token(cls):
        url = settings.TELENITY_TRACKING_AUTH_API
        headers = {
            "Authorization": f"Basic {settings.TELENITY_TRACKING_BASIC_TOKEN.strip()}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(
                url=url,
                headers=headers,
                timeout=30
            )
            # print(settings.TELENITY_TRACKING_BASIC_TOKEN)
            # print(len(settings.TELENITY_TRACKING_BASIC_TOKEN))
            # print("=" * 80)
            # print("TRACKING AUTH")
            # print("Status :", response.status_code)
            # print("Response :", response.text)
            # print("=" * 80)

            if response.status_code != 200:

                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": response.text
                }

            data = response.json()

            access_token = data.get("token")

            if not access_token:

                return {
                    "success": False,
                    "message": "Token not found in API response."
                }

            return {
                "success": True,
                "token": access_token
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }