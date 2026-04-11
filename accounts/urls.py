from django.urls import path
from . import views

urlpatterns = [
     path('<int:order_id>/', views.account_dashboard, name='account_dashboard'),
     path('<int:order_id>/add/', views.add_transaction, name='add_transaction'),
     path('accounts/', views.accounts_list, name='accounts_list')
]