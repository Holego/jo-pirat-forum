import re

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path, reverse_lazy
from django.views.static import serve as serve_static

from board.forms import BanAwareAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=BanAwareAuthenticationForm,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'password/change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change.html',
            success_url=reverse_lazy('password_change_done'),
        ),
        name='password_change',
    ),
    path(
        'password/change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
        name='password_change_done',
    ),
    path('', include('board.urls')),
]

# Django's own conf.urls.static.static() helper silently registers ZERO
# patterns whenever DEBUG=False, regardless of how it's called — which is
# exactly our case here (deployed without a separate web server, e.g.
# directly via gunicorn on a phone, so nothing else serves the uploaded
# avatars/images). Wiring django.views.static.serve() directly bypasses
# that guard so media is actually served in this DEBUG=False deployment.
urlpatterns += [
    re_path(r'^%s(?P<path>.*)$' % re.escape(settings.MEDIA_URL.lstrip('/')), serve_static,
            {'document_root': settings.MEDIA_ROOT}),
]
