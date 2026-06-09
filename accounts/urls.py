from django.urls import path
from . import views

urlpatterns = [

    # 📊 Accounts Dashboard
    #path('', views.accounts_dashboard, name='accounts_dashboard'),

    # 👤 CUSTOMER ACCOUNTS (summary)
    path('customer/', views.customer_accounts, name='customer_accounts'),

    # 📒 CUSTOMER LEDGER (TALLY STYLE DETAIL)
    path('customer/<int:enquiry_id>/ledger/', views.customer_ledger, name='customer_ledger'),

    # 🚚 VEHICLE ACCOUNTS (summary)
    path('vehicle/', views.vehicle_accounts, name='vehicle_accounts'),
    path('vehicle-ledger/<int:vehicle_id>/',views.vehicle_ledger,name='vehicle_ledger'),
    path('edit-vehicle-account/<int:vehicle_id>/',views.edit_vehicle_account,name='edit_vehicle_account'),
    # 🏦 BANK ACCOUNTS
    #path('bank/', views.bank_accounts, name='bank_accounts'),
    path('customer-edit/<int:enquiry_id>/', views.edit_customer_account, name='edit_customer_account'),
    path('customer-payment/<int:enquiry_id>/', views.receive_customer_payment, name='receive_customer_payment'),
    path(
    'vehicle/<int:vehicle_id>/payments/',
    views.vehicle_payments,
    name='vehicle_payments'
),

path(
    'vehicle/<int:vehicle_id>/advance/',
    views.pay_vehicle_advance,
    name='pay_vehicle_advance'
),

path(
    'vehicle/<int:vehicle_id>/balance/',
    views.pay_vehicle_balance,
    name='pay_vehicle_balance'
),
path(
    "vehicle/<int:vehicle_id>/payments/other/",
    views.pay_vehicle_other,
    name="vehicle_other"
),
path(
    "vehicle/<int:vehicle_id>/advance/confirm/",
    views.confirm_vehicle_advance,
    name="confirm_vehicle_advance"
),

path(
    "vehicle/<int:vehicle_id>/advance/success/",
    views.advance_success,
    name="advance_success"
),
path("vehicle/<int:vehicle_id/make_payment/",views.make_payment,name = "make_payment"),

]