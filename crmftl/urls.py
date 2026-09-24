from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from authentications.views import home

urlpatterns = [

    path("admin/", admin.site.urls),

    # Authentication
    path("", include("authentications.urls")),

    # Dashboard
    path("", home, name="home"),

    # Enquiries
    path("enquiry/", include("enquiries.urls")),

    # Orders
    path("orders/", include("orders.urls")),

    # One Page Orders
    path("onepageorder/", include("onepage_order.urls")),

    # Vehicles
    path("vehicles/", include("vehicles.urls")),

    # Accounts
    path("accounts/", include("accounts.urls")),

    # Customers
    path("customers/", include("customers.urls")),

    # Dashboards app
    path("dashboards/", include("dashboards.urls")),

    # Live Tracking
    path("live-tracking/", include("live_tracking.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )