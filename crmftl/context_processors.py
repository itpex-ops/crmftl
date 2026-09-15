# core/context_processors.py

from .menu import ROLE_MENUS

def role_permissions(request):
    if request.user.is_authenticated:
        perms = ROLE_MENUS.get(request.user.role, [])
    else:
        perms = []

    return {'role_perms': perms}

# context_processors.py

from enquiries.models import Notification


def notification_data(request):

    if request.user.is_authenticated:

        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-id')[:5]

        notification_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

    else:

        notifications = []
        notification_count = 0

    return {
        'notifications': notifications,
        'notification_count': notification_count,
    }
