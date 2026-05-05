from django.urls import path
from . import views

urlpatterns = [
    path("manual-order/create/", views.manual_order_create, name="manual_order_create"),
]