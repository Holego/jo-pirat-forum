from django.contrib.auth.models import User
from rest_framework import serializers

from .embeds import extract_embeds
from .models import Category, Post, PrivateMessage, Topic


def _absolute_file_url(request, field_file):
    if not field_file:
        return None
    return request.build_absolute_uri(field_file.url) if request else field_file.url


class UserSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='profile.status', read_only=True)
    status_display = serializers.CharField(source='profile.get_status_display_ru', read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'status', 'status_display', 'avatar']

    def get_avatar(self, user):
        return _absolute_file_url(self.context.get('request'), user.profile.avatar)


class CategorySerializer(serializers.ModelSerializer):
    topic_count = serializers.IntegerField(source='num_topics', read_only=True)
    post_count = serializers.IntegerField(source='num_posts', read_only=True)

    class Meta:
        model = Category
        fields = ['slug', 'name', 'description', 'topic_count', 'post_count']


class TopicSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    reply_count = serializers.SerializerMethodField()
    last_post_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'category', 'author', 'project_url', 'is_pinned', 'is_locked',
            'created_at', 'reply_count', 'last_post_at',
        ]

    def get_reply_count(self, topic):
        # Views annotate num_posts; the first post is the topic itself, not a reply.
        return max(topic.num_posts - 1, 0)


class NewTopicSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    body = serializers.CharField(max_length=20000)
    project_url = serializers.URLField(required=False, allow_blank=True)


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    embeds = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'author', 'body', 'created_at', 'embeds', 'images', 'audio']
        read_only_fields = ['id', 'author', 'created_at']

    def get_embeds(self, post):
        return extract_embeds(post.body)

    def get_images(self, post):
        request = self.context.get('request')
        return [_absolute_file_url(request, img.image) for img in post.images.all()]

    def get_audio(self, post):
        request = self.context.get('request')
        return [_absolute_file_url(request, a.file) for a in post.audio_files.all()]


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)
    recipient = serializers.CharField(source='recipient.username', read_only=True)
    embeds = serializers.SerializerMethodField()

    class Meta:
        model = PrivateMessage
        fields = ['id', 'sender', 'recipient', 'body', 'created_at', 'is_read', 'embeds']
        read_only_fields = ['id', 'sender', 'recipient', 'created_at', 'is_read']

    def get_embeds(self, message):
        return extract_embeds(message.body)


class CredentialsSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, trim_whitespace=False)
