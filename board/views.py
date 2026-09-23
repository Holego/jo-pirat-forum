from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, NewTopicForm, PostForm, PostImageForm, ProfileForm, RegisterForm
from .models import Category, Post, PostImage, Topic

MAX_IMAGES_PER_POST = 4

staff_required = user_passes_test(lambda u: u.is_staff, login_url='login')


def index(request):
    categories = Category.objects.all()
    return render(request, 'board/index.html', {'categories': categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    topics = category.topics.select_related('author').all()
    return render(request, 'board/category_detail.html', {'category': category, 'topics': topics})


def _save_post_images(request, post):
    files = request.FILES.getlist('images')[:MAX_IMAGES_PER_POST]
    for f in files:
        image_form = PostImageForm(files={'image': f})
        if image_form.is_valid():
            PostImage.objects.create(post=post, image=image_form.cleaned_data['image'])
        else:
            messages.warning(request, f'Файл «{f.name}» пропущен: это не изображение или файл слишком большой.')


def _blocked_if_banned(request):
    if request.user.is_authenticated and getattr(request.user, 'profile', None) and request.user.profile.is_banned:
        messages.error(request, 'Ваш аккаунт заблокирован, вы не можете писать на форуме.')
        return True
    return False


def topic_detail(request, slug, pk):
    topic = get_object_or_404(Topic, pk=pk, category__slug=slug)
    posts = topic.posts.select_related('author', 'author__profile').prefetch_related('images').all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        if _blocked_if_banned(request):
            return redirect(topic.get_absolute_url())
        if topic.is_locked:
            messages.error(request, 'Тема закрыта для новых ответов.')
            return redirect(topic.get_absolute_url())
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.save()
            _save_post_images(request, post)
            return redirect(topic.get_absolute_url() + f'#post-{post.pk}')
    else:
        form = PostForm()

    return render(request, 'board/topic_detail.html', {'topic': topic, 'posts': posts, 'form': form})


@login_required
def new_topic(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if _blocked_if_banned(request):
        return redirect('index')
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                topic = form.save(commit=False)
                topic.category = category
                topic.author = request.user
                topic.save()
                post = Post.objects.create(topic=topic, author=request.user, body=form.cleaned_data['body'])
                _save_post_images(request, post)
            return redirect(topic.get_absolute_url())
    else:
        form = NewTopicForm()
    return render(request, 'board/new_topic.html', {'category': category, 'form': form})


@staff_required
def new_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Раздел «{category.name}» создан.')
            return redirect(category.get_absolute_url())
    else:
        form = CategoryForm()
    return render(request, 'board/new_category.html', {'form': form})


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


def profile_detail(request, username):
    profile_user = get_object_or_404(User, username=username)
    topics = Topic.objects.filter(author=profile_user).select_related('category')[:20]
    return render(request, 'board/profile_detail.html', {'profile_user': profile_user, 'topics': topics})


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('profile_detail', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'board/profile_edit.html', {'form': form})
