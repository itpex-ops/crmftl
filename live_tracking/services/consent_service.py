import requests

from django.conf import settings

from live_tracking.models import SMSLog, ApiLog
from .consent_auth_service import ConsentAuthService


class ConsentService:

    @classmethod
    def send_consent(cls, session):

        token = ConsentAuthService.get_tracking_token()

        if not token["success"]:
            return token

        headers = {
            "Authorization": f"Bearer {token['token']}",
            "Accept": "*/*",
            "Content-Type": "application/json"
        }

        payload = {
            "msisdn": session.driver_mobile
        }

        try:

            response = requests.post(
                settings.TELENITY_CONSENT_API,
                json=payload,
                headers=headers,
                timeout=30
            )

            ApiLog.objects.create(
                api_name="Consent API",
                request_data=payload,
                response_data=response.text,
                status_code=response.status_code
            )

            SMSLog.objects.create(
                session=session,
                mobile=session.driver_mobile,
                sms_reference="",
                message="Consent SMS Triggered",
                delivery_status="Pending"
            )

            if response.status_code in [200, 201]:

                session.status = "sms_sent"
                session.save()

                return {
                    "success": True,
                    "message": "Consent SMS Sent"
                }

            return {
                "success": False,
                "message": response.text
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }