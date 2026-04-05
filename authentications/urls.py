from django.urls import path
from . import views
# from .views import (
#     auth_page,
#     admin_reset_requests,
#     approve_reset,
#     reject_reset,
#     reset_password
# )
urlpatterns = [
    path('',  views.auth_page, name='auth'),
    # path('admin-reset-requests/',  views.admin_reset_requests, name='admin_reset_requests'),
    # path('approve-reset/<int:request_id>/',  views.approve_reset, name='approve_reset'),
    # path('reject-reset/<int:request_id>/',  views.reject_reset, name='reject_reset'),
    # path('reset-password/<uuid:token>/',  views.reset_password, name='reset_password'),

    # dashboards
    # path('sales/', views.sales_dashboard, name='sales_dashboard'),
    # path('admin/', views.admin_dashboard, name='admin_dashboard'),
    # path('fleet/', views.fleet_dashboard, name='fleet_dashboard'),
    # path('accounts/', views.accounts_dashboard, name='accounts_dashboard'),
    # path('it/', views.it_dashboard, name='it_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('logout/', views.logout_user,name='logout')
]

