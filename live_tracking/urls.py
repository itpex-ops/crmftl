from django.urls import path
from . import views

urlpatterns = [

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
        "vehicle/<int:session_id>/",
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
    "refresh/<int:session_id>/",
    views.refresh_location,
    name="refresh_location"
),

    path(
    "api-status/",
    views.api_token_status,
    name="api_token_status"
    ),
    path(
    "import-driver/<int:vehicle_id>/",
    views.import_driver,
    name="import_driver",
),
    path(
        "send-consent/<int:session_id>/",
        views.send_consent,
        name="send_consent",
    ),
    path(
        "setup/<int:vehicle_id>/",
        views.live_tracking_setup,
        name="live_tracking_setup",
    ),

    path("test-auth/",
        views.test_tracking_auth,
        name="test_tracking_auth",
    ),
    path(
    "test-consent-auth/",
    views.test_consent_auth,
    name="test_consent_auth"),
    
    path(
        "check-consent/<int:session_id>/",
        views.check_consent,
        name="check_consent",
    ),
    path(
    "test-location/<int:vehicle_id>/",
    views.test_location,
    name="test_location",
),
path(
    "delete/<int:session_id>/",
    views.delete_tracking,
    name="delete_tracking"
),




]
