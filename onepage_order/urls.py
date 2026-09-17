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
        "vehicle-live/<int:pk>/",
        views.vehicle_live,
        name="onepageordervehicle_live",
    ),

    path(
        "vehicle-live/<int:pk>/location/",
        views.vehicle_live_location,
        name="onepageordervehicle_live_location",
    ),
]