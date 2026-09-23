from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import PrivateMessage

ONLINE_MINUTES = 5
RECENT_HOURS = 24
RECENT_LIMIT = 20


def presence(request):
    now = timezone.now()
    online_cutoff = now - timedelta(minutes=ONLINE_MINUTES)
    recent_cutoff = now - timedelta(hours=RECENT_HOURS)

    User = get_user_model()
    online_users = User.objects.filter(profile__last_seen__gte=online_cutoff).select_related('profile')
    recent_users = User.objects.filter(
        profile__last_seen__gte=recent_cutoff, profile__last_seen__lt=online_cutoff
    ).select_related('profile').order_by('-profile__last_seen')[:RECENT_LIMIT]

    return {
        'online_users': online_users,
        'online_count': len(online_users),
        'recent_users': recent_users,
    }


def unread_messages(request):
    if request.user.is_authenticated:
        count = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_message_count': count}
    return {'unread_message_count': 0}
