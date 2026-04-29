from django.urls import path
from . import views
urlpatterns = [
    path('', views.create_ManualOrder, name='create_manual_order'),
]
