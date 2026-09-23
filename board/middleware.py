from django.utils import timezone

from .models import Profile

LAST_SEEN_UPDATE_INTERVAL = 60


class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            profile = getattr(user, 'profile', None)
            if profile is not None:
                now = timezone.now()
                if not profile.last_seen or (now - profile.last_seen).total_seconds() > LAST_SEEN_UPDATE_INTERVAL:
                    Profile.objects.filter(pk=profile.pk).update(last_seen=now)
        return response
