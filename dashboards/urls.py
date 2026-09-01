from django.urls import path
from . import views

urlpatterns = [

    
    path('dashboard/',views.customer_dashboard,name='customer_dashboard'),

    # Live Tracking Dashboard

    path(
        "live-tracking/",
        views.live_tracking_dashboard,
        name="live_tracking_dashboard"
    ),


    path(
        "management/",
        views.management_dashboard,
        name="management_dashboard",
    ),

]