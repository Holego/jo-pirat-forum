from django.contrib import admin

from .models import Category, Post, Topic


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'topic_count']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'created_at', 'is_pinned', 'is_locked']
    list_filter = ['category', 'is_pinned', 'is_locked']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'created_at']
