from django.urls import path
from .views import create_enquiry, enquiry_list,update_pitch,notifications,edit_enquiry
from . import views
from enquiries.consumers import NotificationConsumer
urlpatterns = [
    path('create/', create_enquiry, name='create_enquiry'),
    path('list/', enquiry_list, name='enquiry_list'),
    path('update-pitch/<int:id>/', update_pitch, name='update_pitch'),
    path("update-status/<int:id>/<str:action>/", views.update_enquiry_status, name="update_enquiry_status"), 
    #path('dashboard/',views.enquiry_dashboard,name='enquiry_dashboard'),
    path('notifications/',notifications,name='notifications'),
    path('list/edit/<int:id>/',edit_enquiry,name='edit_enquiry'),
]

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]