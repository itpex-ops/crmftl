from django.urls import path
from . import views


app_name = "onepage_order"


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
        "<int:pk>/",
        views.onepageorder_detail,
        name="onepageorder_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.onepageorder_edit,
        name="onepageorder_edit",
    ),

    path(
        "<int:pk>/delete/",
        views.onepageorder_delete,
        name="onepageorder_delete",
    ),

    # Order workflow tracking
    path(
        "<int:pk>/tracking/",
        views.tracking_page,
        name="tracking_page",
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
    # LIVE TRACKING - LIST
    # =========================================================

    # path(
    #     "live-tracking/",
    #     views.live_tracking_list,
    #     name="live_tracking_list",
    # ),

    # =========================================================
    # LIVE TRACKING - SETUP
    # =========================================================

    # path(
    #     "live-tracking/setup/<int:order_id>/",
    #     views.live_tracking_setup,
    #     name="live_tracking_setup",
    # ),

    # =========================================================
    # IMPORT DRIVER
    # =========================================================

    # path(
    #     "live-tracking/import-driver/<int:order_id>/",
    #     views.import_driver,
    #     name="import_driver",
    # ),

    # =========================================================
    # CONSENT
    # =========================================================

    # path(
    #     "live-tracking/consent/<int:pk>/send/",
    #     views.send_consent,
    #     name="send_consent",
    # ),

    # path(
    #     "live-tracking/consent/<int:pk>/check/",
    #     views.check_consent,
    #     name="check_consent",
    # ),

    # =========================================================
    # LIVE TRACKING PAGE
    # IMPORTANT:
    # pk = TrackingSession PK
    # =========================================================

    # path(
    #     "vehicle-live/<int:pk>/",
    #     views.vehicle_live,
    #     name="vehicle_live",
    # ),

    # =========================================================
    # LIVE LOCATION API
    # =========================================================

    # path(
    #     "vehicle-live/<int:pk>/location/",
    #     views.vehicle_live_location,
    #     name="vehicle_live_location",
    # ),

    # path(
    #     "vehicle-live/<int:pk>/refresh/",
    #     views.refresh_location,
    #     name="refresh_location",
    # ),

    # =========================================================
    # LOCATION HISTORY
    # =========================================================

    # path(
    #     "vehicle-live/<int:pk>/history/",
    #     views.vehicle_history,
    #     name="vehicle_history",
    # ),

    # path(
    #     "vehicle-live/<int:pk>/tracking-history/",
    #     views.tracking_history,
    #     name="tracking_history",
    # ),

    # path(
    #     "vehicle-live/<int:pk>/live-history/",
    #     views.live_tracking_history,
    #     name="live_tracking_history",
    # ),

    # =========================================================
    # TEST LOCATION
    # =========================================================

    # path(
    #     "vehicle-live/<int:pk>/test-location/",
    #     views.test_location,
    #     name="test_location",
    # ),

    # # =========================================================
    # ORDER LOCATION API
    # Optional - useful if order detail needs live location
    # =========================================================

    # path(
    #     "<int:pk>/live-location/",
    #     views.order_live_location,
    #     name="order_live_location",
    # ),

    # =========================================================
    # API / AUTH TEST
    # =========================================================

    # path(
    #     "live-tracking/test-consent-auth/",
    #     views.test_consent_auth,
    #     name="test_consent_auth",
    # ),

    # path(
    #     "live-tracking/test-tracking-auth/",
    #     views.test_tracking_auth,
    #     name="test_tracking_auth",
    # ),

    # path(
    #     "live-tracking/api-token-status/",
    #     views.api_token_status,
    #     name="api_token_status",
    # ),
]