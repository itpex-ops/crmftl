# dashboards/views.py

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from .services import get_management_dashboard_data


def management_access_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())

        # Superuser always has access.
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Your custom User model has a role field.
        role = getattr(request.user, "role", None)

        # Management dashboard access.
        allowed_roles = {
            "admin",
            "it",
        }

        if role not in allowed_roles:
            raise PermissionDenied(
                "You do not have permission to access the Management Dashboard."
            )

        return view_func(request, *args, **kwargs)

    return wrapper


@management_access_required
def management_dashboard(request):

    context = get_management_dashboard_data()

    return render(
        request,
        "dashboards/management_dashboard.html",
        context,
    )