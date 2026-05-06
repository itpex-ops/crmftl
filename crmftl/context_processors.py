# core/context_processors.py

from .menu import ROLE_MENUS

def role_permissions(request):
    if request.user.is_authenticated:
        perms = ROLE_MENUS.get(request.user.role, [])
    else:
        perms = []

    return {'role_perms': perms}