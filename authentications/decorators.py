from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages

def allowed_roles(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect('auth')

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "You are not authorized to access this page")
            return redirect('auth')

        return wrapper
    return decorator
