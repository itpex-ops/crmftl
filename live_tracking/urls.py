from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.live_tracking_dashboard,
        name="live_tracking_dashboard"
    ),

    path(
        "list/",
        views.live_tracking_list,
        name="live_tracking_list"
    ),

    # ALL history (sidebar)
    path(
        "history/",
        views.live_tracking_history,
        name="live_tracking_history"
    ),

    # Single vehicle live page
    path(
        "vehicle/<int:pk>/",
        views.vehicle_live,
        name="vehicle_live"
    ),

    # Single vehicle history
    path(
        "vehicle/<int:pk>/history/",
        views.vehicle_history,
        name="vehicle_history"
    ),

    # path(
    #     "send-sms/<int:vehicle_id>/",
    #     views.send_tracking_sms,
    #     name="send_tracking_sms"
    # ),

    path(
        "refresh/<int:pk>/",
        views.refresh_location,
        name="refresh_location"
    ),

    path(
    "api-status/",
    views.api_token_status,
    name="api_token_status"
),
path(
    "import/<int:vehicle_id>/",
    views.import_driver,
    name="import_driver",
),
path(
    "send-consent/<int:session_id>/",
    views.send_consent,
    name="send_consent",
),


    path("test-auth/",
        views.test_tracking_auth,
        name="test_tracking_auth",
    ),
]
