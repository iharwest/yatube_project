import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_1 = Group.objects.create(
            title='Тестовый заголовок 1',
            description='Тестовое описание 1',
            slug='test-slug-1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовый заголовок 2',
            description='Тестовое описание 2',
            slug='test-slug-2',
        )
        cls.user = User.objects.create_user(username='TestAuthor')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group_1,
            author=cls.user,
            image=cls.uploaded,
        )
        cls.MAIN_PAGE_URL = ('posts:index', None, 'posts/index.html')
        cls.FIRST_GROUP_URL = ('posts:group_list', [cls.group_1.slug],
                               'posts/group_list.html')
        cls.PROFILE_URL = ('posts:profile', [cls.user.username],
                           'posts/profile.html')
        cls.DETAIL_URL = ('posts:post_detail', [cls.post.id],
                          'posts/post_detail.html')
        cls.EDIT_URL = ('posts:post_edit', [cls.post.id],
                        'posts/create_post.html')
        cls.CREATE_URL = ('posts:post_create', None, 'posts/create_post.html')
        cls.EXPECTED_PAGES_URLS = (
            cls.MAIN_PAGE_URL,
            cls.FIRST_GROUP_URL,
            cls.PROFILE_URL
        )
        cls.TEMPLATES_PAGES_NAMES = (
            *cls.EXPECTED_PAGES_URLS,
            cls.DETAIL_URL,
            cls.EDIT_URL,
            cls.CREATE_URL
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаем клиент зарегистрированного пользователя."""
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post_attributes(self, post):
        """Проверка атрибутов поста"""
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.slug, self.group_1.slug)
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.image, self.post.image)

    def chek_index_group_profile_context(self, post):
        """Проверка контекста поста"""
        self.assertEqual(post.group.title, self.group_1.title)
        self.assertEqual(post.group.description, self.group_1.description)
        self.assertEqual(post.id, self.post.id)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, args, html_names in self.TEMPLATES_PAGES_NAMES:
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.authorized_client.get(reverse(address, args=args)),
                    html_names)

    def test_index_group_profile_page_show_correct_context(self):
        """Шаблоны страниц index, group, profile с правильным контекстом."""
        for address, args, _ in self.EXPECTED_PAGES_URLS:
            response = self.authorized_client.get(reverse(address,
                                                          args=args))
            post = response.context['page_obj'][0]
            self.check_post_attributes(post)
            self.chek_index_group_profile_context(post)

    def test_create_edit_pages_show_correct_context(self):
        """Шаблоны страниц создания и редактирования
        постов сформированы с правильным контекстом."""
        urls = [
            self.CREATE_URL,
            self.EDIT_URL
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for address, args, _ in urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(reverse(address,
                                                              args=args))
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_appear_on_expected_pages(self):
        """При создании поста с указанной группой
        пост появляется на ожидаемых страницах."""
        for address, args, _ in self.EXPECTED_PAGES_URLS:
            with self.subTest(address=address):
                response = self.authorized_client.get(reverse(address,
                                                              args=args))
                post = response.context['page_obj'][0]
                self.check_post_attributes(post)

    def test_post_not_in_wrong_group(self):
        """Проверка, что пост не попал в группу,
        для которой не был предназначен."""
        response = self.authorized_client.get(f'/group/{self.group_2.slug}/')
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_cashe_index_page(self):
        """Проверка правильной работы кеширования."""
        form_data = Post.objects.create(
            text='Тестируем кэш',
            group=self.group_2,
            author=self.user,
        )
        main_page = self.MAIN_PAGE_URL[0]

        content_before_delete = self.authorized_client.get(
            reverse(main_page)).content

        form_data.delete()

        content_after_delete = self.authorized_client.get(
            reverse(main_page)).content

        cache.clear()

        content_after_cache_clear = self.authorized_client.get(
            reverse(main_page)).content

        self.assertEqual(
            content_before_delete, content_after_delete
        )
        self.assertNotEqual(
            content_before_delete, content_after_cache_clear
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.user = User.objects.create_user(username='TestAuthor')

        for i in range(13):
            Post.objects.create(
                text=f'Тестовый текст {i+1}',
                group=cls.group,
                author=cls.user
            )

        cls.MAIN_PAGE_URL = ('posts:index', None)
        cls.GROUP_URL = ('posts:group_list', [cls.group.slug])
        cls.PROFILE_URL = ('posts:profile', [cls.user.username])
        cls.PAGE_WITH_PAGINATION = [
            cls.MAIN_PAGE_URL,
            cls.GROUP_URL,
            cls.PROFILE_URL
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверяем, что количество постов на первой странице равно 10."""
        for url, args in self.PAGE_WITH_PAGINATION:
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse(url,
                                                              args=args))
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка количества постов на второй странице."""
        for url, args in self.PAGE_WITH_PAGINATION:
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, args=args) + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor')
        cls.follower = User.objects.create_user(username='TestFollower')
        cls.not_follower = User.objects.create_user(username='TestNotFollower')
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.not_follower
        )
        cls.PROFILE_FOLLOW_URL = (
            'posts:profile_follow', [cls.follower.username])
        cls.PROFILE_UNFOLLOW_URL = (
            'posts:profile_unfollow', [cls.not_follower.username])
        cls.MAIN_PAGE_URL = ('posts:follow_index')

    def setUp(self):
        """Создаем клиент зарегистрированного пользователя."""
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_not_follower = Client()
        self.authorized_not_follower.force_login(self.not_follower)

    def test_follow_author(self):
        """Авторизованный пользователь может
        подписываться на других пользователей."""
        follow_count = Follow.objects.count()
        profile_follow, args = self.PROFILE_FOLLOW_URL
        self.authorized_client.get(
            reverse(
                profile_follow,
                args=args))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user, author=self.follower).exists()
        )

    def test_unfollow_author(self):
        """Авторизованный пользователь может
        удалять пользователей из своих подписок."""
        follow_count = Follow.objects.count()
        profile_unfollow, args = self.PROFILE_UNFOLLOW_URL
        self.authorized_follower.get(
            reverse(
                profile_unfollow,
                args=args))
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower, author=self.not_follower).exists()
        )

    def test_new_post_follow(self):
        """Новая запись пользователя появляется
        в ленте тех, кто на него подписан"""
        profile_follow, args = self.PROFILE_FOLLOW_URL
        self.authorized_client.get(
            reverse(
                profile_follow,
                args=args))
        new_post = Post.objects.create(
            text='Новый тестовый текст',
            author=self.follower
        )
        response = self.authorized_client.get(
            reverse(self.MAIN_PAGE_URL))
        self.assertIn(new_post, response.context['page_obj'].object_list)

    def test_new_post_unfollow(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто на него не подписан"""
        new_post = Post.objects.create(
            text='Новый тестовый текст',
            author=self.user
        )
        response = self.authorized_not_follower.get(
            reverse(self.MAIN_PAGE_URL)
        )
        self.assertNotIn(new_post, response.context['page_obj'].object_list)
