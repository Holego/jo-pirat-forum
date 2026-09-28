from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Category, Post, PrivateMessage, Topic

PASSWORD = 'pw-for-tests-123'


class ApiTestCase(APITestCase):
    def setUp(self):
        cache.clear()  # throttle counters live in the cache
        self.user = User.objects.create_user('pirate', password=PASSWORD)
        self.category = Category.objects.create(name='Флуд', slug='flood')
        self.topic = Topic.objects.create(category=self.category, title='Мемы', author=self.user)
        Post.objects.create(topic=self.topic, author=self.user, body='Первый пост https://x.com/cat.gif')

    def auth(self, user=None):
        token, _ = Token.objects.get_or_create(user=user or self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')


class RootAndAuthTests(ApiTestCase):
    def test_root_identifies_the_api(self):
        data = self.client.get('/api/').json()
        self.assertEqual(data['api'], 'tor-forum')
        self.assertEqual(data['version'], 1)

    def test_login_returns_token_that_authenticates(self):
        response = self.client.post('/api/auth/login/', {'username': 'pirate', 'password': PASSWORD})
        self.assertEqual(response.status_code, 200)
        token = response.json()['token']
        self.assertEqual(response.json()['user']['username'], 'pirate')

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(self.client.get('/api/me/').json()['username'], 'pirate')

    def test_login_with_wrong_password_fails(self):
        response = self.client.post('/api/auth/login/', {'username': 'pirate', 'password': 'nope'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.json())

    def test_banned_user_cannot_log_in(self):
        self.user.profile.is_banned = True
        self.user.profile.save()
        response = self.client.post('/api/auth/login/', {'username': 'pirate', 'password': PASSWORD})
        self.assertEqual(response.status_code, 403)

    def test_register_creates_account_and_logs_in(self):
        response = self.client.post('/api/auth/register/', {'username': 'newbie', 'password': 'Sup3r-secret-pass'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newbie').exists())
        self.assertTrue(response.json()['token'])

    def test_register_rejects_weak_password_with_readable_error(self):
        response = self.client.post('/api/auth/register/', {'username': 'newbie', 'password': '123'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.json()['errors'])
        self.assertTrue(response.json()['detail'])

    def test_register_rejects_taken_username(self):
        response = self.client.post('/api/auth/register/', {'username': 'pirate', 'password': 'Sup3r-secret-pass'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json()['errors'])

    def test_logout_revokes_token(self):
        self.auth()
        self.assertEqual(self.client.post('/api/auth/logout/').status_code, 204)
        self.assertEqual(self.client.get('/api/me/').status_code, 401)

    def test_auth_endpoints_are_throttled(self):
        for _ in range(30):
            self.client.post('/api/auth/login/', {'username': 'pirate', 'password': 'nope'})
        response = self.client.post('/api/auth/login/', {'username': 'pirate', 'password': PASSWORD})
        self.assertEqual(response.status_code, 429)


class ForumReadTests(ApiTestCase):
    def test_categories_are_public_with_counts(self):
        data = self.client.get('/api/categories/').json()
        self.assertEqual(data, [{
            'slug': 'flood', 'name': 'Флуд', 'description': '', 'topic_count': 1, 'post_count': 1,
        }])

    def test_topic_list_is_public_and_puts_pinned_first(self):
        pinned = Topic.objects.create(category=self.category, title='Правила', author=self.user, is_pinned=True)
        Post.objects.create(topic=pinned, author=self.user, body='Не флудить (шутка)')
        results = self.client.get('/api/categories/flood/topics/').json()['results']
        self.assertEqual([t['title'] for t in results], ['Правила', 'Мемы'])
        self.assertEqual(results[1]['reply_count'], 0)

    def test_reading_posts_requires_account(self):
        self.assertEqual(self.client.get(f'/api/topics/{self.topic.pk}/posts/').status_code, 401)

    def test_posts_include_embeds(self):
        self.auth()
        post = self.client.get(f'/api/topics/{self.topic.pk}/posts/').json()['results'][0]
        self.assertEqual(post['author']['username'], 'pirate')
        self.assertEqual(post['embeds'], [{'kind': 'image', 'url': 'https://x.com/cat.gif'}])
        self.assertEqual(post['images'], [])

    def test_last_page_shortcut(self):
        self.auth()
        for i in range(35):
            Post.objects.create(topic=self.topic, author=self.user, body=f'ответ {i}')
        data = self.client.get(f'/api/topics/{self.topic.pk}/posts/?page=last').json()
        self.assertEqual(data['count'], 36)
        self.assertEqual(data['results'][-1]['body'], 'ответ 34')


class ForumWriteTests(ApiTestCase):
    def test_reply(self):
        self.auth()
        response = self.client.post(f'/api/topics/{self.topic.pk}/posts/', {'body': 'Ответ из приложения'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.topic.posts.count(), 2)

    def test_anonymous_cannot_reply(self):
        response = self.client.post(f'/api/topics/{self.topic.pk}/posts/', {'body': 'hi'})
        self.assertEqual(response.status_code, 401)

    def test_cannot_reply_to_locked_topic(self):
        self.topic.is_locked = True
        self.topic.save()
        self.auth()
        response = self.client.post(f'/api/topics/{self.topic.pk}/posts/', {'body': 'hi'})
        self.assertEqual(response.status_code, 403)

    def test_banned_user_cannot_write(self):
        self.user.profile.is_banned = True
        self.user.profile.save()
        self.auth()
        response = self.client.post(f'/api/topics/{self.topic.pk}/posts/', {'body': 'hi'})
        self.assertEqual(response.status_code, 403)

    def test_new_topic(self):
        self.auth()
        response = self.client.post('/api/categories/flood/topics/', {'title': 'Новая тема', 'body': 'Текст'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['title'], 'Новая тема')
        topic = Topic.objects.get(pk=response.json()['id'])
        self.assertEqual(topic.posts.get().body, 'Текст')

    def test_new_topic_requires_account(self):
        response = self.client.post('/api/categories/flood/topics/', {'title': 'x', 'body': 'y'})
        self.assertEqual(response.status_code, 401)


class MessagesTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.other = User.objects.create_user('matey', password=PASSWORD)
        PrivateMessage.objects.create(sender=self.other, recipient=self.user, body='Привет https://x.com/a.png')

    def test_conversation_list_counts_unread(self):
        self.auth()
        data = self.client.get('/api/messages/').json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['user']['username'], 'matey')
        self.assertEqual(data[0]['unread_count'], 1)

    def test_reading_thread_marks_it_read(self):
        self.auth()
        thread = self.client.get('/api/messages/matey/').json()
        self.assertEqual(thread[0]['embeds'], [{'kind': 'image', 'url': 'https://x.com/a.png'}])
        self.assertEqual(self.client.get('/api/me/').json()['unread_messages'], 0)

    def test_send_message(self):
        self.auth()
        response = self.client.post('/api/messages/matey/', {'body': 'Йо-хо-хо'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['recipient'], 'matey')
        self.assertTrue(PrivateMessage.objects.filter(sender=self.user, recipient=self.other).exists())

    def test_cannot_message_yourself(self):
        self.auth()
        self.assertEqual(self.client.post('/api/messages/pirate/', {'body': 'hi'}).status_code, 400)
