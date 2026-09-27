from .models import SchoolSetting, Notification


def global_school_context(request):
    """
    Context processor to provide global school settings and user notifications to all templates.
    """
    context = {
        'school_settings': SchoolSetting.get_settings(),
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }

    if request.user.is_authenticated:
        # User specific or broadcast notifications
        notifs = Notification.objects.filter(models_q_filter(request.user))
        context['unread_notifications_count'] = notifs.filter(is_read=False).count()
        context['recent_notifications'] = notifs[:5]
        context['user_role'] = request.user.role if hasattr(request.user, 'role') else 'STAFF'

    return context


def models_q_filter(user):
    from django.db.models import Q
    return Q(user=user) | Q(user__isnull=True)
