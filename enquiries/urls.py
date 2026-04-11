from django.urls import path
from .views import create_enquiry, enquiry_list, edit_enquiry,update_pitch
from . import views
urlpatterns = [
    path('create/', create_enquiry, name='create_enquiry'),
    path('list/', enquiry_list, name='enquiry_list'),
    path('edit/<int:id>/', edit_enquiry, name='edit_enquiry'),
    path('update-pitch/<int:enquiry_id>/<str:status>/', update_pitch, name='update_pitch'),
    path("update-status/<int:id>/<str:action>/", views.update_enquiry_status, name="update_enquiry_status"),
]

