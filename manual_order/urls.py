from django.urls import path
from . import views
urlpatterns = [
    path('create-order/', views.create_manual_order, name='create_manual_order'),
]