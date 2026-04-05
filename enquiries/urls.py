from django.urls import path
from .views import create_enquiry, enquiry_list,delete_enquiry,confirm_enquiry, edit_enquiry,update_pitch,convert_to_order

urlpatterns = [
    path('create/', create_enquiry, name='create_enquiry'),
    path('list/', enquiry_list, name='enquiry_list'),
    path('edit/<int:id>/', edit_enquiry, name='edit_enquiry'),
     path('update-pitch/<int:enquiry_id>/<str:status>/', update_pitch, name='update_pitch'),
    path('enquiry/delete/<int:id>/',delete_enquiry , name = "delete_enquiry"),
    path('confirm-enquiry/<int:id>/', confirm_enquiry, name='confirm_enquiry'),
    #path('reject-pitch/<int:enquiry_id>/', reject_pitch, name='reject_pitch'),
    #path('approve-pitch/<int:enquiry_id>/', approve_pitch, name='approve_pitch'),
    #path("convert-to-order/<int:id>/", convert_to_order, name="convert_to_order"),
]
