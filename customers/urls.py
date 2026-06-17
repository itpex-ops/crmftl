from django.urls import path
from . import views

urlpatterns = [

    path("", views.customer_list, name="customer_list"),

    path("create/", views.customer_create, name="customer_create"),

    path("edit/<int:pk>/", views.customer_update, name="customer_update"),

    path("delete/<int:pk>/", views.customer_delete, name="customer_delete"),

    path('dashboard/',views.customer_dashboard,name='customer_dashboard'),

]