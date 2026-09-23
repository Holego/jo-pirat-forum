from django.contrib import admin

from .models import Category, Post, PostAudio, PostImage, Profile, ProfileLink, Topic


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'topic_count']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'created_at', 'is_pinned', 'is_locked']
    list_filter = ['category', 'is_pinned', 'is_locked']


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0


class PostAudioInline(admin.TabularInline):
    model = PostAudio
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'created_at']
    inlines = [PostImageInline, PostAudioInline]


class ProfileLinkInline(admin.TabularInline):
    model = ProfileLink
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'is_banned']
    list_filter = ['status', 'is_banned']
    search_fields = ['user__username']
    actions = ['ban_users', 'unban_users']
    inlines = [ProfileLinkInline]

    @admin.action(description='Забанить выбранных пользователей')
    def ban_users(self, request, queryset):
        updated = queryset.update(is_banned=True, status=Profile.BANNED)
        self.message_user(request, f'Заблокировано пользователей: {updated}')

    @admin.action(description='Разбанить выбранных пользователей')
    def unban_users(self, request, queryset):
        updated = queryset.update(is_banned=False, status=Profile.MEMBER)
        self.message_user(request, f'Разблокировано пользователей: {updated}')
