"""JSON API for native clients (e.g. the tor-forum-client mobile app).

Mirrors what the web UI allows: categories and topic lists are public, reading
a topic needs an account, writing is blocked for banned users. Clients
authenticate with `Authorization: Token <key>` from /api/auth/login/.
"""
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .forms import RegisterForm
from .models import Category, Post, PrivateMessage, Topic
from .serializers import (
    CategorySerializer,
    CredentialsSerializer,
    MessageSerializer,
    NewTopicSerializer,
    PostSerializer,
    TopicSerializer,
    UserSerializer,
)

API_NAME = 'tor-forum'
API_VERSION = 1
BANNED_MESSAGE = 'Ваш аккаунт заблокирован на этом форуме.'


def _is_banned(user):
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.is_banned)


class NotBanned(permissions.BasePermission):
    message = BANNED_MESSAGE

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or not _is_banned(request.user)


class WriteRequiresAccount(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_authenticated


def _auth_response(request, user, http_status=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {'token': token.key, 'user': UserSerializer(user, context={'request': request}).data},
        status=http_status,
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    """Lets a client check that a site speaks this API before showing it natively."""
    return Response({
        'api': API_NAME,
        'version': API_VERSION,
        'name': 'Jo Pirat Forum',
        'registration': True,
        'uploads': settings.FORUM_ALLOW_UPLOADS,
    })


class AuthThrottleMixin:
    # Over Tor every request comes from 127.0.0.1, so this is a forum-wide
    # cap on login/registration attempts rather than a per-person one.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'
    permission_classes = [permissions.AllowAny]


class LoginView(AuthThrottleMixin, APIView):
    def post(self, request):
        credentials = CredentialsSerializer(data=request.data)
        credentials.is_valid(raise_exception=True)
        user = authenticate(request, **credentials.validated_data)
        if user is None:
            return Response({'detail': 'Неверное имя пользователя или пароль.'}, status=status.HTTP_400_BAD_REQUEST)
        if _is_banned(user):
            return Response({'detail': BANNED_MESSAGE}, status=status.HTTP_403_FORBIDDEN)
        return _auth_response(request, user)


class RegisterView(AuthThrottleMixin, APIView):
    def post(self, request):
        password = request.data.get('password', '')
        form = RegisterForm(data={
            'username': request.data.get('username', ''),
            'email': request.data.get('email', ''),
            'password1': password,
            'password2': password,
        })
        if not form.is_valid():
            errors = {
                ('password' if field.startswith('password') else field): [str(e) for e in field_errors]
                for field, field_errors in form.errors.items()
            }
            first_error = next(iter(errors.values()))[0]
            return Response({'detail': first_error, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        user = form.save()
        return _auth_response(request, user, http_status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user, context={'request': request}).data
        data['unread_messages'] = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
        return Response(data)


class CategoryList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.annotate(
            num_topics=Count('topics', distinct=True),
            num_posts=Count('topics__posts', distinct=True),
        )


def _topics_with_stats():
    return Topic.objects.select_related('author', 'author__profile', 'category').annotate(
        num_posts=Count('posts'),
        last_post_at=Max('posts__created_at'),
    )


class CategoryTopicList(generics.ListCreateAPIView):
    """Topics of one category, pinned first, then by latest activity. POST starts a new topic."""

    permission_classes = [WriteRequiresAccount, NotBanned]
    serializer_class = TopicSerializer

    def get_category(self):
        return get_object_or_404(Category, slug=self.kwargs['slug'])

    def get_queryset(self):
        return _topics_with_stats().filter(category=self.get_category()).order_by('-is_pinned', '-last_post_at')

    def create(self, request, *args, **kwargs):
        category = self.get_category()
        new_topic = NewTopicSerializer(data=request.data)
        new_topic.is_valid(raise_exception=True)
        data = new_topic.validated_data
        with transaction.atomic():
            topic = Topic.objects.create(
                category=category, author=request.user,
                title=data['title'], project_url=data.get('project_url', ''),
            )
            Post.objects.create(topic=topic, author=request.user, body=data['body'])
        topic = _topics_with_stats().get(pk=topic.pk)
        return Response(self.get_serializer(topic).data, status=status.HTTP_201_CREATED)


class TopicDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TopicSerializer

    def get_queryset(self):
        return _topics_with_stats()


class TopicPostList(generics.ListCreateAPIView):
    """Posts of a topic, oldest first (`?page=last` jumps to the newest). POST replies."""

    permission_classes = [permissions.IsAuthenticated, NotBanned]
    serializer_class = PostSerializer

    def get_topic(self):
        return get_object_or_404(Topic, pk=self.kwargs['pk'])

    def get_queryset(self):
        return self.get_topic().posts.select_related('author', 'author__profile').prefetch_related(
            'images', 'audio_files'
        ).order_by('created_at', 'id')

    def perform_create(self, serializer):
        topic = self.get_topic()
        if topic.is_locked:
            raise PermissionDenied('Тема закрыта для новых ответов.')
        serializer.save(topic=topic, author=self.request.user)


class ConversationList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        context = {'request': request}
        return Response([
            {
                'user': UserSerializer(c['user'], context=context).data,
                'last_message': MessageSerializer(c['last_message'], context=context).data,
                'unread_count': c['unread_count'],
            }
            for c in PrivateMessage.conversations_for(request.user)
        ])


class ConversationThread(generics.ListCreateAPIView):
    """The whole conversation with one user, oldest first. Reading it marks it as read."""

    permission_classes = [permissions.IsAuthenticated, NotBanned]
    serializer_class = MessageSerializer
    pagination_class = None

    def get_other(self):
        other = get_object_or_404(User, username=self.kwargs['username'])
        if other == self.request.user:
            raise ValidationError({'detail': 'Нельзя написать самому себе.'})
        return other

    def get_queryset(self):
        return PrivateMessage.thread_between(self.request.user, self.get_other())

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        PrivateMessage.objects.filter(
            sender=self.get_other(), recipient=request.user, is_read=False
        ).update(is_read=True)
        return response

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, recipient=self.get_other())
