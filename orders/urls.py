from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),    
    path('assign/<int:order_id>/', views.assign_vehicle, name='assign_vehicle'),
    path('pricing/<int:id>/', views.order_detail, name='order_detail'),
    path('convert/<int:enquiry_id>/', views.convert_to_order, name='convert_to_order'),
     path("tracking/<int:order_id>/", views.tracking_update, name="tracking_page"),
    path("create/<int:enquiry_id>/", views.create_order_from_enquiry, name="create_order"),
    path('view_order/<int:order_id>/', views.view_orders,name= 'view_order'),
]

