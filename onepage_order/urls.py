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
    # LIVE TRACKING LIST
    # =========================================================

    path(
        "onepageorders/",
        views.live_tracking_list,
        name="live_tracking_list",
    ),


    # =========================================================
    # LIVE TRACKING SETUP
    # =========================================================

    path(
        "onepageorders/setup/<int:order_id>/",
        views.onepageorderlive_tracking_setup,
        name="onepageorderlive_tracking_setup",
    ),

    path(
        "onepageorders/import-driver/<int:order_id>/",
        views.import_driver,
        name="import_driver",
    ),


    # =========================================================
    # LIVE TRACKING
    #
    # pk = TrackingSession PK
    # =========================================================

    path(
        "onepageorders/<int:pk>/",
        views.vehicle_live,
        name="onepageordervehicle_live",
    ),

    path(
        "onepageorders/<int:pk>/location/",
        views.vehicle_live_location,
        name="onepageordervehicle_live_location",
    ),

    path(
        "onepageorders/<int:pk>/refresh/",
        views.refresh_location,
        name="refresh_location",
    ),

    path(
        "onepageorders/<int:pk>/history/",
        views.vehicle_history,
        name="vehicle_history",
    ),

    path(
        "onepageorders/<int:pk>/tracking-history/",
        views.tracking_history,
        name="tracking_history",
    ),

    path(
        "onepageorders/<int:pk>/live-history/",
        views.live_tracking_history,
        name="live_tracking_history",
    ),

    path(
        "onepageorders/<int:pk>/test-location/",
        views.test_location,
        name="test_location",
    ),

    path(
        "onepageorders/<int:pk>/delete/",
        views.delete_tracking,
        name="delete_tracking",
    ),


    # =========================================================
    # CONSENT
    #
    # pk = TrackingSession PK
    # =========================================================

    path(
        "onepageorders/consent/<int:pk>/",
        views.send_consent,
        name="send_consent",
    ),

    path(
        "onepageorders/consent/check/<int:pk>/",
        views.check_consent,
        name="check_consent",
    ),


    # =========================================================
    # API / AUTH TEST
    # =========================================================

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