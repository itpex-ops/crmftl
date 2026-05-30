from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.manual_order_create, name="manual_order_create"),
    path(
        'existing-order/<int:id>/',
        views.view_existing_order,
        name='view_existing_order'
    ),
]