from django.urls import path
from . import views

urlpatterns = [

    path(
        "auth/",
        views.auth_page,
        name="auth",
    ),

    path(
        "logout/",
        views.logout_user,
        name="logout",
    ),

    path(
        "clear-session/",
        views.clear_session,
        name="clear_session",
    ),
]