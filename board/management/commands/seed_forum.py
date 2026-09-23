import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from board.models import Category, Post, Profile, Topic

CATEGORIES = [
    ('Мои проекты', 'Проекты, которые я разрабатываю и выкладываю на GitHub', 0),
    ('Вопросы и помощь', 'Задавайте вопросы по коду и разработке', 1),
    ('Общий раздел', 'Обсуждение разработки, инструментов, технологий', 2),
    ('Флуд', 'Оффтоп и флуд обо всём на свете', 3),
]


class Command(BaseCommand):
    help = 'Создаёт стартовые категории и приветственную тему'

    def handle(self, *args, **options):
        User = get_user_model()
        author, _ = User.objects.get_or_create(
            username='admin',
            defaults={'is_staff': True, 'is_superuser': True},
        )
        if not author.has_usable_password():
            admin_password = os.environ.get('DJANGO_ADMIN_PASSWORD')
            if admin_password:
                author.set_password(admin_password)
                author.save()
                self.stdout.write(self.style.SUCCESS('Пароль admin установлен из DJANGO_ADMIN_PASSWORD'))
            else:
                self.stdout.write(self.style.WARNING(
                    'У пользователя admin ещё нет пароля. Установите его: '
                    'python manage.py changepassword admin '
                    '(или задайте DJANGO_ADMIN_PASSWORD перед запуском seed_forum).'
                ))
        Profile.objects.filter(user=author).update(status=Profile.MODERATOR)

        for name, description, order in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=name, defaults={'description': description, 'order': order}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создана категория: {name}'))

        projects = Category.objects.get(name='Мои проекты')
        if not projects.topics.exists():
            topic = Topic.objects.create(
                category=projects,
                title='Добро пожаловать на Jo Pirat Forum',
                author=author,
            )
            Post.objects.create(
                topic=topic,
                author=author,
                body=(
                    'Привет! Это форум, где я выкладываю свои проекты и делюсь тем, '
                    'над чем работаю. Заходите, читайте, оставляйте комментарии.'
                ),
            )
            self.stdout.write(self.style.SUCCESS('Создана приветственная тема'))

        self.stdout.write(self.style.SUCCESS('Готово.'))
