from django.urls import path
from . import views

urlpatterns = [

    # 📊 Accounts Dashboard
    path('management_dashboard', views.management_dashboard, name='management_dashboard'),
    
    path('dashboard/',views.customer_dashboard,name='customer_dashboard'),

    # Live Tracking Dashboard

    path(
        "live-tracking/",
        views.live_tracking_dashboard,
        name="live_tracking_dashboard"
    ),
    

]