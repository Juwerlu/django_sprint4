from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, DateTimeField
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class PublishedModel(models.Model):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        abstract = True


class DateModel(models.Model):
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True


class Location(PublishedModel, DateModel):
    name = models.CharField('Название места', max_length=settings.MAX_LENGTH)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ('name', )

    def __str__(self):
        return self.name


class Category(PublishedModel, DateModel):
    title = models.CharField('Заголовок', max_length=settings.MAX_LENGTH)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('title', )

    def __str__(self):
        return self.title


class PostQuerySet(models.QuerySet):

    def annotated(self):
        return self.order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comments'))

    def published(self):
        return self.filter(
            is_published=True,
            pub_date__date__lte=timezone.now(),
            category__is_published=True
        ).select_related('author', 'category', 'location').annotated()


class PublishedPostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db).published()


class AnnotatedPostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db).annotated()


class Post(PublishedModel, DateModel):
    objects = models.Manager()
    published = PublishedPostManager()
    annotated = AnnotatedPostManager()
    title = models.CharField('Заголовок', max_length=settings.MAX_LENGTH)
    text = models.TextField('Текст')
    pub_date = DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем '
            '— можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE, blank=True,
        related_name='posts',
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL, null=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL, null=True, blank=False,
        related_name='posts',
        verbose_name='Категория'
    )
    image = models.ImageField('Фото', upload_to='posts_images', blank=True)

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    def get_absolute_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.author.get_username()},
        )

    def __str__(self):
        return self.title


class Comment(PublishedModel, DateModel):
    text = models.TextField(
        verbose_name='Комментарий',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор публикации',
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at', )
