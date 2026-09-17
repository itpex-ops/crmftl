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

    # =========================================================
    # PAYMENTS
    # =========================================================

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

    # =========================================================
    # LIVE TRACKING
    # =========================================================

    path(
        "onepagevehicle-live/<int:pk>/",
        views.onepageordervehicle_live,
        name="onepageordervehicle_live",
    ),

    path(
        "onepagevehicle-live/<int:pk>/location/",
        views.onepageordervehicle_live_location,
        name="onepageordervehicle_live_location",
    ),


    path(
        "admin-margin/",
        views.admin_margin,
        name="admin_margin",
    ),


    # =========================================================
    # LIVE TRACKING LIST / SETUP
    # =========================================================

    path(
        "onepagelive-tracking/",
        views.onepageorderlive_tracking_list,
        name="onepageorderlive_tracking_list",
    ),

    path(
        "live-tracking/setup/<int:order_id>/",
        views.onepagelive_tracking_setup,
        name="onepagelive_tracking_setup",
    ),

    path(
        "live-tracking/import-driver/<int:order_id>/",
        views.import_driver,
        name="import_driver",
    ),

    path(
        "live-tracking/<int:pk>/delete/",
        views.delete_tracking,
        name="delete_tracking",
    ),


    # =========================================================
    # CONSENT
    # =========================================================

    path(
        "live-tracking/consent/<int:session_id>/",
        views.send_consent,
        name="send_consent",
    ),

    path(
        "live-tracking/consent/check/<int:session_id>/",
        views.check_consent,
        name="check_consent",
    ),


    # =========================================================
    # LIVE TRACKING PAGE
    # `session_id` = TrackingSession PK
    # =========================================================

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
        "live-tracking/test-consent-auth/",
        views.test_consent_auth,
        name="test_consent_auth",
    ),

    path(
        "live-tracking/test-tracking-auth/",
        views.test_tracking_auth,
        name="test_tracking_auth",
    ),

    path(
        "live-tracking/api-token-status/",
        views.api_token_status,
        name="api_token_status",
    ),
]
