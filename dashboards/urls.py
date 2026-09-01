# dashboards/urls.py

from django.urls import path

from . import views


urlpatterns = [

    path(
        "management/",
        views.management_dashboard,
        name="management_dashboard",
    ),

]