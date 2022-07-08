from django.test import TestCase, Client

from ..models import Comment, Group, Post, User


class PostGroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.comment = Comment.objects.create(
            text='Тестовый текст комментария' * 3,
            post=cls.post,
            author=cls.user,
        )

    def setUp(self):
        """Создаем клиент зарегистрированного пользователя."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.post.text[:15], str(self.post))
        self.assertEqual(self.group.title, str(self.group))
        self.assertEqual(self.comment.text, str(self.comment))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
            'title': 'Название группы',
            'slug': 'Идентификатор',
            'description': 'Описание группы',
            'image': 'Изображение'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                models = {
                    Post: self.post,
                    Group: self.group
                }
                for response, object in models.items():
                    if hasattr(response, field):
                        self.assertEqual(
                            object._meta.get_field(field).verbose_name,
                            expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
            'title': 'Введите название группы',
            'slug': 'Введите идентификатор',
            'description': 'Введите описание группы',
            'image': 'Загрузите изображение'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                models = {
                    Post: self.post,
                    Group: self.group
                }
                for response, object in models.items():
                    if hasattr(response, field):
                        self.assertEqual(
                            object._meta.get_field(field).help_text,
                            expected_value)

    def test_verbose_name_comment(self):
        """verbose_name в полях совпадает с ожидаемым."""
        comment = self.comment
        field_verboses = {
            'text': 'Текст комментария',
            'created': 'Дата создания',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_comment(self):
        """help_text в полях совпадает с ожидаемым."""
        comment = self.comment
        field_help_texts = {
            'text': 'Введите текст комментария',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).help_text, expected_value)
