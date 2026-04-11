from django.urls import path
from . import views

urlpatterns = [
    path('',views.all_assigned_vehicles,name ='all_assigned_vehicles'),
    path('order/<int:order_id>/vehicles/', views.assigned_vehicles, name='assigned_vehicles'),
     path('order/<int:order_id>/assign/', views.assign_vehicle, name='assign_vehicle'),
    path('vehicle/<int:vehicle_id>/edit/', views.edit_vehicle, name='edit_vehicle'),
    path('vehicle/<int:vehicle_id>/delete/', views.delete_vehicle, name='delete_vehicle'),
    #path('vehicle/<int:vehicle_id>/tracking/', views.tracking_page , name='tracking_page')
    #path('tracking/<int:vehicle_id>/', views.tracking_page, name='tracking_page'),
    path('vehicles/update-inline/', views.update_vehicle_inline, name='update_vehicle_inline'),
#path('tracking/update-ajax/', views.update_tracking_ajax, name='update_tracking_ajax'),
path('tracking/<int:vehicle_id>/', views.tracking_page, name='tracking_page'),
path('tracking/update-ajax/', views.update_tracking_ajax, name='update_tracking_ajax'),
]