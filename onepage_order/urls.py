from django.urls import path
from . import views
urlpatterns=[
path('onepageorders/list/',views.onepageorder_list,name='onepageorder_list'),
path('onepageorders/new/',views.onepageorder_create,name='onepageorder_create'), 
path('onepageorders/<int:pk>/',views.onepageorder_detail,name='onepageorder_detail'), 
path('onepageorders/<int:pk>/edit/',views.onepageorder_edit,name='onepageorder_edit'), 
path('vehicle-payments/',views.vehicle_payments,name='vehicle_payments'), 
path('customer-payments/',views.customer_payments,name='customer_payments'), 
path('admin-margin/',views.admin_margin,name='admin_margin'),
]
