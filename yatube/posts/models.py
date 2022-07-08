from core.models import CreatedModel

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Введите название группы')
    slug = models.SlugField(
        max_length=100,
        db_index=True,
        unique=True,
        verbose_name='Идентификатор',
        help_text='Введите идентификатор')
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание группы',)

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор')
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='group_posts',
        verbose_name='Группа',
        help_text='Выберите группу')
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name='Изображение',
        help_text='Загрузите изображение'
    )

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )

    def __str__(self):
        return self.text


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Отслеживаемый автор'
    )

    def __str__(self):
        return f'{self.user} follows {self.author}'
