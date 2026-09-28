import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .embeds import MAX_EMBEDS_PER_MESSAGE, extract_embeds
from .models import Category, Post, PostImage, PrivateMessage, Topic

# 1x1 transparent GIF
TINY_GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00'
    b',\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class ExtractEmbedsTests(TestCase):
    def test_detects_images_gifs_video_and_audio(self):
        text = (
            'смотри https://i.imgur.com/cat.png и https://media.tenor.com/x/tenor.gif\n'
            'видео https://example.com/clip.webm, музыка http://example.onion/song.mp3'
        )
        self.assertEqual(extract_embeds(text), [
            {'kind': 'image', 'url': 'https://i.imgur.com/cat.png'},
            {'kind': 'image', 'url': 'https://media.tenor.com/x/tenor.gif'},
            {'kind': 'video', 'url': 'https://example.com/clip.webm'},
            {'kind': 'audio', 'url': 'http://example.onion/song.mp3'},
        ])

    def test_ignores_non_media_links_and_non_http_schemes(self):
        text = 'https://github.com/Holego/jo-pirat-forum ftp://host/pic.png javascript:alert(1).png'
        self.assertEqual(extract_embeds(text), [])

    def test_extension_is_matched_case_insensitively_and_before_query_string(self):
        self.assertEqual(
            extract_embeds('https://cdn.example.com/Pic.JPG?width=500&v=2'),
            [{'kind': 'image', 'url': 'https://cdn.example.com/Pic.JPG?width=500&v=2'}],
        )

    def test_trailing_punctuation_is_not_part_of_the_link(self):
        self.assertEqual(
            extract_embeds('Вот (https://example.com/a.gif). И ещё https://example.com/b.png!'),
            [
                {'kind': 'image', 'url': 'https://example.com/a.gif'},
                {'kind': 'image', 'url': 'https://example.com/b.png'},
            ],
        )

    def test_imgur_gifv_becomes_mp4(self):
        self.assertEqual(
            extract_embeds('https://i.imgur.com/abc.gifv'),
            [{'kind': 'video', 'url': 'https://i.imgur.com/abc.mp4'}],
        )

    def test_duplicates_are_shown_once(self):
        self.assertEqual(len(extract_embeds('https://x.com/a.png https://x.com/a.png')), 1)

    def test_number_of_embeds_is_capped(self):
        text = ' '.join(f'https://x.com/{i}.png' for i in range(MAX_EMBEDS_PER_MESSAGE + 5))
        self.assertEqual(len(extract_embeds(text)), MAX_EMBEDS_PER_MESSAGE)

    def test_quotes_and_angle_brackets_end_the_link(self):
        self.assertEqual(
            extract_embeds('https://x.com/a.png"onerror="alert(1) <https://x.com/b.gif>'),
            [
                {'kind': 'image', 'url': 'https://x.com/a.png'},
                {'kind': 'image', 'url': 'https://x.com/b.gif'},
            ],
        )


class ForumTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pirate', password='pw-for-tests-123')
        self.category = Category.objects.create(name='Флуд', slug='flood')
        self.topic = Topic.objects.create(category=self.category, title='Мемы', author=self.user)
        Post.objects.create(topic=self.topic, author=self.user, body='Первый пост')
        self.client.force_login(self.user)


class PostEmbedRenderingTests(ForumTestCase):
    def test_image_link_is_shown_under_the_post_and_stays_a_clickable_link(self):
        Post.objects.create(topic=self.topic, author=self.user, body='лол https://i.imgur.com/cat.gif')
        response = self.client.get(self.topic.get_absolute_url())
        self.assertContains(response, '<a href="https://i.imgur.com/cat.gif" rel="nofollow">')
        self.assertContains(response, '<img src="https://i.imgur.com/cat.gif" alt="" loading="lazy">', html=True)

    def test_video_and_audio_links_get_players(self):
        Post.objects.create(
            topic=self.topic, author=self.user, body='https://i.imgur.com/x.gifv https://example.com/s.ogg'
        )
        response = self.client.get(self.topic.get_absolute_url())
        self.assertContains(response, '<video src="https://i.imgur.com/x.mp4"')
        self.assertContains(response, '<audio src="https://example.com/s.ogg"')

    def test_injection_attempt_is_escaped(self):
        Post.objects.create(
            topic=self.topic, author=self.user, body='https://x.com/a.png"onerror="alert(1)<script>alert(2)</script>'
        )
        response = self.client.get(self.topic.get_absolute_url())
        self.assertNotContains(response, '<script>alert(2)')
        self.assertNotContains(response, 'onerror="alert(1)"')
        self.assertContains(response, '<img src="https://x.com/a.png"')

    def test_post_without_media_links_has_no_embed_block(self):
        response = self.client.get(self.topic.get_absolute_url())
        self.assertNotContains(response, 'post-embeds')

    def test_private_messages_show_embeds_too(self):
        other = User.objects.create_user('matey', password='pw-for-tests-123')
        PrivateMessage.objects.create(sender=other, recipient=self.user, body='https://x.com/meme.webp')
        response = self.client.get('/messages/matey/')
        self.assertContains(response, '<img src="https://x.com/meme.webp"')


class UploadSettingTests(ForumTestCase):
    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

    def _reply_with_image(self):
        image = SimpleUploadedFile('pixel.gif', TINY_GIF, content_type='image/gif')
        return self.client.post(self.topic.get_absolute_url(), {'body': 'с картинкой', 'images': [image]})

    def test_uploads_are_off_by_default(self):
        with self.settings(MEDIA_ROOT=self.media_root):
            response = self.client.get(self.topic.get_absolute_url())
            self.assertNotContains(response, 'name="images"')
            self.assertContains(response, 'прямой ссылкой')

            self._reply_with_image()
        self.assertTrue(Post.objects.filter(body='с картинкой').exists())
        self.assertEqual(PostImage.objects.count(), 0)

    @override_settings(FORUM_ALLOW_UPLOADS=True)
    def test_uploads_can_be_turned_back_on(self):
        with self.settings(MEDIA_ROOT=self.media_root):
            response = self.client.get(self.topic.get_absolute_url())
            self.assertContains(response, 'name="images"')

            self._reply_with_image()
        self.assertEqual(PostImage.objects.count(), 1)

    def test_new_topic_form_hides_file_inputs_when_uploads_are_off(self):
        response = self.client.get(f'/c/{self.category.slug}/new/')
        self.assertNotContains(response, 'name="images"')
        self.assertNotContains(response, 'name="audio"')
