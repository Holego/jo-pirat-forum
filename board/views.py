from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NewTopicForm, PostForm, RegisterForm
from .models import Category, Post, Topic


def index(request):
    categories = Category.objects.all()
    return render(request, 'board/index.html', {'categories': categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    topics = category.topics.select_related('author').all()
    return render(request, 'board/category_detail.html', {'category': category, 'topics': topics})


def topic_detail(request, slug, pk):
    topic = get_object_or_404(Topic, pk=pk, category__slug=slug)
    posts = topic.posts.select_related('author').all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        if topic.is_locked:
            messages.error(request, 'Тема закрыта для новых ответов.')
            return redirect(topic.get_absolute_url())
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.save()
            return redirect(topic.get_absolute_url() + f'#post-{post.pk}')
    else:
        form = PostForm()

    return render(request, 'board/topic_detail.html', {'topic': topic, 'posts': posts, 'form': form})


@login_required
def new_topic(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                topic = form.save(commit=False)
                topic.category = category
                topic.author = request.user
                topic.save()
                Post.objects.create(topic=topic, author=request.user, body=form.cleaned_data['body'])
            return redirect(topic.get_absolute_url())
    else:
        form = NewTopicForm()
    return render(request, 'board/new_topic.html', {'category': category, 'form': form})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Добро пожаловать на форум!')
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})
