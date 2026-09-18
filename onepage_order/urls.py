from django.urls import path
from . import views

urlpatterns = [
    # =========================================================
    # ORDERS
    # =========================================================
    path(
        "list/",
        views.onepageorder_list,
        name="onepageorder_list",
    ),

    path(
        "new/",
        views.onepageorder_create,
        name="onepageorder_create",
    ),

    path(
        "<int:pk>/edit/",
        views.onepageorder_edit,
        name="onepageorder_edit",
    ),

    path(
        "<int:pk>/tracking/",
        views.tracking_page,
        name="onepageorder_tracking",
    ),

    path(
        "<int:pk>/delete/",
        views.onepageorder_delete,
        name="onepageorder_delete",
    ),

    path(
        "<int:pk>/",
        views.onepageorder_detail,
        name="onepageorder_detail",
    ),

    path(
        "vehicle-payments/",
        views.vehicle_payments,
        name="vehicle_payments",
    ),

    path(
        "customer-payments/",
        views.customer_payments,
        name="customer_payments",
    ),

    path(
        "admin-margin/",
        views.admin_margin,
        name="admin_margin",
         ),

    path(
            "setup/<int:vehicle_id>/",
            views.live_tracking_setup,
            name="onepageorderlive_tracking_setup",
        ),

    path(
        "vehicle-live/<int:pk>/location/",
        views.vehicle_live_location,
        name="onepageordervehicle_live_location",
    ),

#     # =========================================================
#     # LIVE TRACKING
#     # =========================================================

    path(
        "vehicle-live/<int:pk>/",
        views.vehicle_live,
        name="onepageordervehicle_live",
    ),
        path(
        "",
        views.live_tracking_list,
        name="live_tracking_list",
    ),



#     # =========================================================
#     # LIVE TRACKING LIST / SETUP
#     # =========================================================

    path(
        "import-driver/<int:order_id>/",
        views.import_driver,
        name="import_driver",
    ),

    path(
        "<int:pk>/delete/",
        views.delete_tracking,
        name="delete_tracking",
    ),


    # =========================================================
    # CONSENT
    # =========================================================

    path(
        "consent/<int:session_id>/",
        views.send_consent,
        name="send_consent",
    ),

    path(
        "consent/check/<int:session_id>/",
        views.check_consent,
        name="check_consent",
    ),


    # =========================================================
    # LIVE TRACKING PAGE
    # `session_id` = TrackingSession PK
    # =========================================================

    path(
        "vehicle-live/<int:session_id>/",
        views.vehicle_live,
        name="vehicle_live",
    ),

    path(
        "vehicle-live/<int:session_id>/location/",
        views.vehicle_live_location,
        name="vehicle_live_location",
    ),

    path(
        "vehicle-live/<int:session_id>/refresh/",
        views.refresh_location,
        name="refresh_location",
    ),

    path(
        "vehicle-live/<int:session_id>/history/",
        views.vehicle_history,
        name="vehicle_history",
    ),

    # # Alias
    path(
        "vehicle-live/<int:session_id>/tracking-history/",
        views.tracking_history,
        name="tracking_history",
    ),

    # # Alias
    path(
        "vehicle-live/<int:session_id>/live-history/",
        views.live_tracking_history,
        name="live_tracking_history",
    ),

    # # Test current location
    path(
        "vehicle-live/<int:session_id>/test-location/",
        views.test_location,
        name="test_location",
    ),


    # # =========================================================
    # # API / AUTH TEST
    # # =========================================================

    path(
        "test-consent-auth/",
        views.test_consent_auth,
        name="test_consent_auth",
    ),

    path(
        "test-tracking-auth/",
        views.test_tracking_auth,
        name="test_tracking_auth",
    ),

    path(
        "api-token-status/",
        views.api_token_status,
        name="api_token_status",
    ),
]
