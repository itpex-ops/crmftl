from banking.models import ApiLog


class ApiLogService:

    @staticmethod
    def create_log(
        api_name,
        endpoint,
        method,
        request_data=None,
        response_data=None,
        status_code=None,
        response_time=None,
        success=False,
    ):
        return ApiLog.objects.create(
            api_name=api_name,
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=response_data,
            status_code=status_code,
            response_time=response_time,
            success=success,
        )