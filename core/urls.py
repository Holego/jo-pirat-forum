from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

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
    path('', include('board.urls')),
]

# Served unconditionally (not just in DEBUG) because this app is deployed
# without a separate web server (e.g. directly via gunicorn on a phone) —
# there is nothing else in front of it to serve uploaded avatars/images.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
