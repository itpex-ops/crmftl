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
        "reports/payments/",
        views.payment_report,
        name="payment_report",
    ),

    path("payment_report_pdf/",views.payment_report_pdf,name='payment_report_pdf'),
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
    # ONE PAGE ORDER LIVE TRACKING
    # =========================================================

    path(
        "tracking-list/",
        views.onepageorder_tracking_list,
        name="onepageorder_tracking_list",
    ),

    # pk = Order PK
    path(
        "<int:pk>/setup/",
        views.onepageorder_tracking_setup,
        name="onepageorder_tracking_setup",
    ),

    path(
        "import-driver/<int:pk>/",
        views.import_driver,
        name="onepageorder_import_driver",
    ),

    # pk = TrackingSession PK
    path(
        "vehicle-live/<int:pk>/",
        views.vehicle_live,
        name="onepageordervehicle_live",
    ),

    path(
        "vehicle-live/<int:pk>/location/",
        views.vehicle_live_location,
        name="onepageordervehicle_live_location",
    ),

    path(
        "vehicle-live/<int:pk>/refresh/",
        views.refresh_location,
        name="onepageordervehicle_refresh",
    ),

    path(
        "vehicle-live/<int:pk>/history/",
        views.vehicle_history,
        name="onepageordervehicle_history",
    ),

    path(
        "vehicle-live/<int:pk>/tracking-history/",
        views.tracking_history,
        name="onepageordervehicle_tracking_history",
    ),

    path(
        "vehicle-live/<int:pk>/live-history/",
        views.live_tracking_history,
        name="onepageordervehicle_live_history",
    ),

    path(
        "vehicle-live/<int:pk>/test-location/",
        views.test_location,
        name="onepageordervehicle_test_location",
    ),

    path(
        "vehicle-live/<int:pk>/delete/",
        views.delete_tracking,
        name="onepageordervehicle_delete",
    ),


    # =========================================================
    # CONSENT
    # pk = TrackingSession PK
    # =========================================================

    path(
        "consent/<int:pk>/",
        views.onepageorder_send_consent,
        name="onepageorder_send_consent",
    ),

    path(
        "consent/check/<int:pk>/",
        views.onepageorder_check_consent,
        name="onepageorder_check_consent",
    ),


    # =========================================================
    # TEST APIs
    # =========================================================

    path(
        "test-consent-auth/",
        views.test_consent_auth,
        name="onepageorder_test_consent_auth",
    ),

    path(
        "test-tracking-auth/",
        views.test_tracking_auth,
        name="onepageorder_test_tracking_auth",
    ),

    path(
        "api-token-status/",
        views.api_token_status,
        name="onepageorder_api_token_status",
    ),
]