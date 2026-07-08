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
        views.tracking_history,
        name="live_tracking_history"
    ),

    # Single vehicle live page
    path(
        "vehicle/<int:pk>/",
        views.vehicle_live,
        name="vehicle_live"
    ),

    # Single vehicle history
#     path(
#         "vehicle/<int:pk>/history/",
#         views.tracking_history,
# ,
#         name="vehicle_history"
#     ),

    path(
        "send-sms/<int:vehicle_id>/",
        views.send_tracking_sms,
        name="send_tracking_sms"
    ),

    path(
        "refresh/<int:pk>/",
        views.refresh_location,
        name="refresh_location"
    ),
]