from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.author,
        )
        cls.MAIN_PAGE_URL = '/'
        cls.GROUP_URL = f'/group/{cls.group.slug}/'
        cls.AUTHOR_PROFILE_URL = f'/profile/{cls.author.username}/'
        cls.USER_PROFILE_URL = f'/profile/{cls.user.username}/'
        cls.POST_URL = f'/posts/{cls.post.id}/'
        cls.EDIT_URL = f'/posts/{cls.post.id}/edit/'
        cls.CREATE_URL = '/create/'
        cls.NOT_EXIST = '/group/not_exist/'
        cls.TEST_URLS_FOR_ALL_USERS = [
            cls.MAIN_PAGE_URL,
            cls.GROUP_URL,
            cls.POST_URL,
            cls.AUTHOR_PROFILE_URL
        ]
        cls.TEST_URLS_FOR_REDIRECT = [
            cls.EDIT_URL,
            cls.CREATE_URL
        ]
        cls.TEST_URLS_CORRECT_TEMPLATE = [
            *cls.TEST_URLS_FOR_ALL_USERS,
            *cls.TEST_URLS_FOR_REDIRECT,
            cls.USER_PROFILE_URL
        ]

    def setUp(self):
        """Создаем клиент пользователя."""
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        """Проверка адресов страниц, доступных всем пользователям"""
        urls = [*self.TEST_URLS_FOR_ALL_USERS]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_authorized(self):
        """Проверка доступности страниц для авторизованного пользователя"""
        response = self.authorized_client.get(self.CREATE_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous(self):
        """Страницы создания и редактированияпостов
         перенаправляют анонимного пользователя."""
        for url in self.TEST_URLS_FOR_REDIRECT:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, f'{reverse("login")}?next={url}'
                )

    def test_post_edit_url_accessible_for_author(self):
        """Проверка возможности редактирования поста его автором."""
        response = self.authorized_author.get(self.EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_not_author(self):
        """Страница редактирования поста перенаправляет
        пользователя, не являющегося автором поста."""
        response = self.authorized_client.get(self.EDIT_URL)
        self.assertRedirects(response, self.POST_URL)

    def test_wrong_url_returns_404(self):
        """Проверка вывода ошибки 404 при запросе
        к несуществующей странице."""
        response = self.guest_client.get(self.NOT_EXIST)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url in self.TEST_URLS_CORRECT_TEMPLATE:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
