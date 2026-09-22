from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify


class Profile(models.Model):
    NEWBIE = 'newbie'
    MEMBER = 'member'
    VETERAN = 'veteran'
    MODERATOR = 'moderator'
    BANNED = 'banned'
    STATUS_CHOICES = [
        (NEWBIE, 'Новичок'),
        (MEMBER, 'Участник'),
        (VETERAN, 'Ветеран'),
        (MODERATOR, 'Модератор'),
        (BANNED, 'Заблокирован'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)
    bio = models.TextField('О себе', blank=True)
    website = models.URLField('Сайт / портфолио', blank=True)
    github = models.URLField('GitHub', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NEWBIE)
    is_banned = models.BooleanField('Забанен', default=False)
    ban_reason = models.CharField('Причина бана', max_length=255, blank=True)

    def __str__(self):
        return f'Профиль {self.user.username}'

    def get_status_display_ru(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])

    @property
    def topic_count(self):
        return self.topics.count()

    @property
    def post_count(self):
        return Post.objects.filter(topic__category=self).count()

    @property
    def last_post(self):
        return Post.objects.filter(topic__category=self).order_by('-created_at').first()


class Topic(models.Model):
    category = models.ForeignKey(Category, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=210, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='topics', on_delete=models.CASCADE)
    project_url = models.URLField('Ссылка на проект', blank=True)
    is_pinned = models.BooleanField('Закреплено', default=False)
    is_locked = models.BooleanField('Закрыто', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)[:200]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('topic_detail', args=[self.category.slug, self.pk])

    @property
    def reply_count(self):
        return self.posts.count() - 1

    @property
    def last_post(self):
        return self.posts.order_by('-created_at').first()


class Post(models.Model):
    topic = models.ForeignKey(Topic, related_name='posts', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='posts', on_delete=models.CASCADE)
    body = models.TextField('Сообщение')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} @ {self.topic}'


class PostImage(models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField('Изображение', upload_to='post_images/%Y/%m/')

    def __str__(self):
        return f'Изображение к посту #{self.post_id}'
